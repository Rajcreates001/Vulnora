"""Generate JSON and summary for URL scan reports."""

from datetime import datetime, timezone
from typing import Any, Dict, List


def generate_report_summary(
    target_url: str,
    vulnerabilities: List[Dict[str, Any]],
    security_posture_score: int,
    pages_count: int,
    scan_id: str,
) -> Dict[str, Any]:
    """Executive summary and scope for the report."""
    sev_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for v in vulnerabilities:
        s = v.get("severity", "Medium")
        sev_counts[s] = sev_counts.get(s, 0) + 1
    return {
        "scan_id": scan_id,
        "target_url": target_url,
        "scan_date": datetime.now(timezone.utc).isoformat(),
        "executive_summary": (
            f"Security assessment of {target_url} identified {len(vulnerabilities)} potential vulnerabilities. "
            f"Security posture score: {security_posture_score}/100. "
            f"{sev_counts.get('Critical', 0)} Critical, {sev_counts.get('High', 0)} High, "
            f"{sev_counts.get('Medium', 0)} Medium, {sev_counts.get('Low', 0)} Low."
        ),
        "scope": {
            "target": target_url,
            "pages_crawled": pages_count,
            "total_findings": len(vulnerabilities),
        },
        "methodology": [
            "Automated crawl to discover pages, forms, and API endpoints.",
            "Deterministic payload injection (SQLi, XSS, path traversal, open redirect).",
            "Anomaly detection via response status, content, and reflection.",
            "Exploit validation and structured justification.",
        ],
        "security_posture_score": security_posture_score,
        "severity_counts": sev_counts,
    }


def generate_report_json(
    scan_id: str,
    target_url: str,
    vulnerabilities: List[Dict[str, Any]],
    attack_paths: List[Dict[str, Any]],
    summary: Dict[str, Any],
    agent_logs: List[Dict[str, Any]],
    crawl_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Full standardized output format for API and download."""
    return {
        "scan_id": scan_id,
        "target_url": target_url,
        "security_posture_score": summary.get("security_posture_score", 0),
        "vulnerabilities": vulnerabilities,
        "attack_paths": attack_paths,
        "summary": summary,
        "agent_logs": agent_logs,
        "discovered_endpoints": {
            "pages": crawl_data.get("pages", []),
            "forms": crawl_data.get("forms", []),
            "api_endpoints": crawl_data.get("api_endpoints", []),
        },
    }
