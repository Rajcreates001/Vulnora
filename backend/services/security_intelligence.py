"""Security Intelligence Index — computes a 0-100 score from scan results.

Factors:
  - Exploitability (vuln severity distribution)
  - Patch quality (patches provided vs needed)
  - Secure coding patterns (absence of common anti-patterns)
  - Code complexity proxy (file count, language diversity)
  - Risk awareness (presence of input validation, auth patterns)
  - Documentation quality proxy
"""

from typing import Any, Dict, List


def compute_security_intelligence_index(
    vulnerabilities: List[Dict[str, Any]],
    files: List[Dict[str, Any]],
    patches: List[Dict[str, Any]] | None = None,
    exploits: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Return Security Intelligence Index (0-100) with breakdown."""
    patches = patches or []
    exploits = exploits or []
    total_vulns = len(vulnerabilities)
    total_files = max(len(files), 1)

    # ── 1. Exploitability Score (0-100, higher = more secure) ──
    severity_weights = {"Critical": 10, "High": 6, "Medium": 3, "Low": 1}
    weighted_vuln_score = sum(
        severity_weights.get(v.get("severity", "Medium"), 3)
        for v in vulnerabilities
    )
    max_possible = total_files * 2  # rough normalizer
    exploitability_score = max(0, 100 - min(100, (weighted_vuln_score / max(max_possible, 1)) * 100))

    # ── 2. Patch Quality Score ──
    if total_vulns > 0:
        patched_count = sum(1 for p in patches if p.get("patched_code"))
        patch_quality = (patched_count / total_vulns) * 100
    else:
        patch_quality = 100.0

    # ── 3. Secure Coding Patterns Score ──
    critical_count = sum(1 for v in vulnerabilities if v.get("severity") == "Critical")
    high_count = sum(1 for v in vulnerabilities if v.get("severity") == "High")
    vuln_density = total_vulns / total_files
    if vuln_density < 0.1:
        secure_coding = 95.0
    elif vuln_density < 0.3:
        secure_coding = 75.0
    elif vuln_density < 0.6:
        secure_coding = 50.0
    else:
        secure_coding = max(10.0, 30.0 - critical_count * 5)

    # ── 4. Code Complexity Score ──
    languages = set(f.get("language", "unknown") for f in files)
    language_count = len(languages - {"unknown"})
    complexity_score = min(100, 60 + language_count * 5 + min(total_files, 40))

    # ── 5. Risk Awareness Score ──
    vuln_types = [v.get("vulnerability_type", "").lower() for v in vulnerabilities]
    injection_count = sum(1 for t in vuln_types if "injection" in t)
    auth_issues = sum(1 for t in vuln_types if "auth" in t or "authentication" in t)
    hardcoded = sum(1 for t in vuln_types if "hardcoded" in t or "secret" in t or "credential" in t)
    risk_deductions = injection_count * 8 + auth_issues * 10 + hardcoded * 12
    risk_awareness = max(0, 100 - risk_deductions)

    # ── 6. Documentation Quality Proxy ──
    doc_files = sum(1 for f in files if f.get("file_path", "").lower().endswith((".md", ".txt", ".rst")))
    doc_ratio = doc_files / total_files
    if doc_ratio > 0.05:
        documentation = 80.0
    elif doc_ratio > 0.02:
        documentation = 60.0
    else:
        documentation = 30.0

    # ── Composite Score ──
    weights = {
        "exploitability": 0.25,
        "patch_quality": 0.15,
        "secure_coding": 0.25,
        "complexity": 0.10,
        "risk_awareness": 0.15,
        "documentation": 0.10,
    }
    scores = {
        "exploitability": round(exploitability_score, 1),
        "patch_quality": round(patch_quality, 1),
        "secure_coding": round(secure_coding, 1),
        "complexity": round(complexity_score, 1),
        "risk_awareness": round(risk_awareness, 1),
        "documentation": round(documentation, 1),
    }
    composite = sum(scores[k] * weights[k] for k in weights)

    return {
        "security_intelligence_index": round(composite, 1),
        "breakdown": scores,
        "summary": _generate_summary(composite, total_vulns, critical_count, high_count),
        "total_vulnerabilities": total_vulns,
        "critical_count": critical_count,
        "high_count": high_count,
        "files_analyzed": total_files,
    }


def _generate_summary(score: float, total_vulns: int, critical: int, high: int) -> str:
    if score >= 85:
        return f"Excellent security posture. {total_vulns} minor issues detected."
    elif score >= 70:
        return f"Good security practices with room for improvement. {total_vulns} vulnerabilities found."
    elif score >= 50:
        return f"Moderate security concerns. {critical} critical and {high} high-severity issues require attention."
    elif score >= 30:
        return f"Significant security weaknesses. {critical} critical vulnerabilities demand immediate remediation."
    else:
        return f"Critical security posture. {total_vulns} vulnerabilities including {critical} critical issues. Immediate action required."
