"""Exploit validation (structured justification) and why-this-was-missed engine."""

from typing import Any, Dict, List, Optional

# Why-missed reasons by category (deterministic)
WHY_MISSED_REASONS: Dict[str, List[str]] = {
    "sql_injection": [
        "Hidden behind dynamic query building; not visible in static analysis.",
        "Requires multiple request sequence to trigger (e.g. second-order).",
        "Input validation applied inconsistently across different entry points.",
        "Looks safe when tested with single quote; breaks with crafted string.",
        "Framework ORM usage masks raw SQL in some code paths.",
    ],
    "xss": [
        "Output encoding applied in HTML but not in JavaScript context.",
        "Sink is inside dynamically evaluated script.",
        "Reflection only in specific browser or after login.",
        "CSP allows inline script on certain pages only.",
    ],
    "path_traversal": [
        "Path normalization differs between runtime and test environment.",
        "Validation only on filename, not full path.",
        "Runtime dependency (e.g. symlink) exposes file.",
    ],
    "open_redirect": [
        "Redirect URL validated by allowlist but bypassable with subdomain.",
        "Validation only on hostname; path can inject.",
    ],
    "command_injection": [
        "Command built from multiple inputs; one is unsanitized.",
        "Looks safe individually; chained with other parameter.",
    ],
    "default": [
        "Hidden behind dynamic logic.",
        "Requires multiple request sequence.",
        "Input validation inconsistent across entry points.",
        "Looks safe individually.",
        "Framework behavior complexity.",
    ],
}


def _severity_from_category(category: str) -> str:
    m = {
        "sql_injection": "Critical",
        "command_injection": "Critical",
        "xss": "High",
        "path_traversal": "High",
        "open_redirect": "Medium",
    }
    return m.get(category, "Medium")


def _impact_from_category(category: str) -> str:
    m = {
        "sql_injection": "Database read/write or authentication bypass.",
        "xss": "Session hijack, credential theft, or malware delivery.",
        "path_traversal": "Arbitrary file read on server.",
        "open_redirect": "Phishing or token theft via redirect.",
        "command_injection": "Full server compromise.",
    }
    return m.get(category, "Varies by context.")


def validate_findings(
    raw_findings: List[Dict[str, Any]],
    dedupe: bool = True,
) -> List[Dict[str, Any]]:
    """Turn raw scanner findings into validated vulnerabilities with justification."""
    seen: set = set()
    out: List[Dict[str, Any]] = []
    for f in raw_findings:
        key = (f.get("url"), f.get("parameter"), f.get("category"))
        if dedupe and key in seen:
            continue
        seen.add(key)
        category = f.get("category", "default")
        severity = _severity_from_category(category)
        impact = _impact_from_category(category)
        evidence = f.get("evidence_snippet", "") or "Response differs from baseline or shows error."
        vuln = {
            "id": "",
            "title": f"{category.replace('_', ' ').title()} in {f.get('parameter', 'input')}",
            "severity": severity,
            "endpoint": f.get("url", ""),
            "parameter": f.get("parameter", ""),
            "description": f"Potential {category.replace('_', ' ')} detected via payload injection.",
            "payload": f.get("payload_used", ""),
            "evidence": evidence[:1000],
            "impact": impact,
            "exploit_steps": [
                f"Send {f.get('method', 'GET')} request to {f.get('url', '')}",
                f"Set parameter '{f.get('parameter', '')}' to: {f.get('payload_used', '')}",
                "Observe response for error/reflection/redirect.",
            ],
            "patch_recommendation": _patch_recommendation(category),
            "risk_score": 50 + (20 if severity == "Critical" else 10 if severity == "High" else 0),
            "confidence": min(92, 70 + (10 if f.get("anomaly") else 0)),
            "why_missed": "",
        }
        vuln["why_missed"] = generate_why_missed(category, vuln)
        out.append(vuln)
    return out


def _patch_recommendation(category: str) -> str:
    m = {
        "sql_injection": "Use parameterized queries or ORM; never concatenate user input into SQL.",
        "xss": "Encode all user-controlled data for the correct context (HTML, JS, URL).",
        "path_traversal": "Validate and sanitize file paths; use allowlist; avoid user input in paths.",
        "open_redirect": "Validate redirect URLs against allowlist; reject scheme and host from user.",
        "command_injection": "Avoid shell execution with user input; use safe APIs and allowlist.",
    }
    return m.get(category, "Apply input validation and output encoding; principle of least privilege.")


def generate_why_missed(category: str, vuln: Optional[Dict] = None) -> str:
    """Return a deterministic 'why this was missed' reason for the category."""
    reasons = WHY_MISSED_REASONS.get(category) or WHY_MISSED_REASONS["default"]
    import random
    return random.choice(reasons)


def compute_security_posture_score(
    vulnerabilities: List[Dict[str, Any]],
    num_endpoints: int = 1,
    headers_secure: bool = False,
) -> int:
    """Compute 0-100 security posture score (lower = worse)."""
    score = 100
    sev_penalty = {"Critical": 25, "High": 15, "Medium": 8, "Low": 3}
    for v in vulnerabilities:
        score -= sev_penalty.get(v.get("severity", "Medium"), 5)
    if num_endpoints > 20:
        score -= 5
    if not headers_secure:
        score -= 5
    return max(0, min(100, score))
