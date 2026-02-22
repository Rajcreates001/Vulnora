"""Skill Inflation Detection — compares resume claims vs actual repo findings.

Identifies contradictions between what a candidate claims on their resume
and what the security scan actually finds in their code repositories.
"""

from typing import Any, Dict, List
import re


# Security-related claim keywords mapped to vulnerability types that contradict them
CLAIM_TO_VULN_MAP = {
    "secure backend": ["SQL Injection", "Command Injection", "Authentication Bypass",
                       "Hardcoded Credentials", "Insecure Deserialization"],
    "secure api": ["SQL Injection", "Authentication Bypass", "IDOR",
                   "Missing Rate Limiting", "Broken Access Control"],
    "security expert": ["SQL Injection", "XSS", "CSRF", "Hardcoded Credentials",
                        "Authentication Bypass", "Command Injection"],
    "owasp": ["SQL Injection", "XSS", "CSRF", "Broken Access Control",
              "Security Misconfiguration", "Insecure Deserialization"],
    "input validation": ["SQL Injection", "XSS", "Command Injection",
                         "Path Traversal", "LDAP Injection"],
    "authentication": ["Authentication Bypass", "Hardcoded Credentials",
                       "Weak Password", "Missing Authentication"],
    "encryption": ["Hardcoded Credentials", "Weak Encryption", "Plaintext Secrets",
                   "Missing Encryption"],
    "secure coding": ["SQL Injection", "XSS", "Hardcoded Credentials",
                      "Buffer Overflow", "Race Condition"],
    "penetration testing": ["SQL Injection", "XSS", "CSRF", "Command Injection",
                            "Path Traversal"],
    "cryptography": ["Weak Encryption", "Hardcoded Credentials", "Insecure Random"],
    "devops security": ["Hardcoded Credentials", "Security Misconfiguration",
                        "Exposed Secrets", "Missing Encryption"],
    "devsecops": ["Hardcoded Credentials", "Security Misconfiguration",
                  "Exposed Secrets", "Missing Authentication"],
}


def detect_skill_inflation(
    resume_text: str,
    vulnerabilities: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Detect mismatches between resume security claims and repo reality.

    Returns a structured result with contradictions, severity, and overall
    skill inflation score.
    """
    resume_lower = resume_text.lower()
    vuln_types = [v.get("vulnerability_type", "").lower() for v in vulnerabilities]
    vuln_titles = [v.get("title", "").lower() for v in vulnerabilities]
    vuln_severities = [v.get("severity", "Medium") for v in vulnerabilities]

    contradictions: List[Dict[str, Any]] = []

    for claim_keyword, contradicting_vulns in CLAIM_TO_VULN_MAP.items():
        # Check if resume mentions this security skill
        if claim_keyword not in resume_lower:
            continue

        # Find matching vulnerabilities in the repo
        matching_vulns = []
        for i, (vtype, vtitle, vsev) in enumerate(zip(vuln_types, vuln_titles, vuln_severities)):
            for cv in contradicting_vulns:
                if cv.lower() in vtype or cv.lower() in vtitle:
                    matching_vulns.append({
                        "vulnerability": vulnerabilities[i].get("title", "Unknown"),
                        "type": vulnerabilities[i].get("vulnerability_type", "Unknown"),
                        "severity": vsev,
                        "file": vulnerabilities[i].get("file_path", ""),
                    })
                    break

        if matching_vulns:
            # Determine contradiction severity from worst vuln
            sev_order = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
            worst = max(matching_vulns, key=lambda x: sev_order.get(x["severity"], 0))

            contradictions.append({
                "claim": f"Resume claims expertise in: '{claim_keyword}'",
                "evidence": f"Repository contains {len(matching_vulns)} contradicting vulnerabilities",
                "severity": worst["severity"],
                "matching_vulnerabilities": matching_vulns[:5],  # Limit display
                "explanation": _generate_explanation(claim_keyword, matching_vulns),
            })

    # Compute overall inflation score (0-100, higher = more inflated)
    if not contradictions:
        inflation_score = 0.0
        verdict = "consistent"
    else:
        sev_scores = {"Critical": 25, "High": 15, "Medium": 8, "Low": 3}
        inflation_score = min(100, sum(
            sev_scores.get(c["severity"], 5) for c in contradictions
        ))
        if inflation_score >= 60:
            verdict = "significant_inflation"
        elif inflation_score >= 30:
            verdict = "moderate_inflation"
        else:
            verdict = "minor_inflation"

    return {
        "skill_inflation_score": round(inflation_score, 1),
        "verdict": verdict,
        "contradictions": contradictions,
        "total_contradictions": len(contradictions),
        "summary": _generate_summary(verdict, contradictions),
    }


def _generate_explanation(claim: str, vulns: List[Dict[str, Any]]) -> str:
    vuln_types = set(v["type"] for v in vulns)
    types_str = ", ".join(list(vuln_types)[:3])
    sev_counts = {}
    for v in vulns:
        sev_counts[v["severity"]] = sev_counts.get(v["severity"], 0) + 1

    parts = []
    if "Critical" in sev_counts:
        parts.append(f"{sev_counts['Critical']} critical")
    if "High" in sev_counts:
        parts.append(f"{sev_counts['High']} high-severity")

    severity_str = " and ".join(parts) if parts else f"{len(vulns)}"
    return (
        f"Candidate claims '{claim}' expertise, but their repository "
        f"contains {severity_str} vulnerabilities including {types_str}. "
        f"This indicates a gap between stated skills and demonstrated practices."
    )


def _generate_summary(verdict: str, contradictions: List[Dict[str, Any]]) -> str:
    if verdict == "consistent":
        return "Resume claims are consistent with repository security practices. No skill inflation detected."
    elif verdict == "minor_inflation":
        return f"Minor discrepancies found between resume claims and codebase. {len(contradictions)} claims could not be fully verified."
    elif verdict == "moderate_inflation":
        return f"Moderate skill inflation detected. {len(contradictions)} resume claims contradict actual security practices in the repository."
    else:
        return f"Significant skill inflation detected. {len(contradictions)} major contradictions between resume security claims and repository vulnerabilities."
