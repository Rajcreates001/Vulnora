"""
URL Scan agent workflow (LangGraph-style).
Flow: Crawler -> Endpoint Analysis -> Vulnerability Detection -> Exploit Validation -> Risk -> Insight -> Report.
Reuses existing webscan pipeline; steps are named for agent_log compatibility.
"""

from typing import Any, Dict, List, Optional

from webscan.crawler.crawler import crawl_url, CrawlResult
from webscan.scanner.scanner import run_scan
from webscan.analyzer.analyzer import validate_findings, compute_security_posture_score
from webscan.report.report import generate_report_summary, generate_report_json


async def run_url_scan_workflow(
    scan_id: str,
    target_url: str,
    credentials: Optional[Dict[str, str]] = None,
    on_log: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Run the full URL scan pipeline (crawler -> scan -> analyze -> report).
    on_log(agent_name, message) is called for each step for agent_logs.
    """
    def log(agent: str, msg: str):
        if on_log:
            on_log(agent, msg)

    log("crawler_agent", "Crawling target and discovering endpoints...")
    crawl = await crawl_url(
        target_url,
        max_pages=25,
        use_playwright=bool(credentials),
        credentials=credentials,
        timeout=15.0,
    )
    crawl_data = crawl.to_dict()
    log("crawler_agent", f"Discovered {len(crawl.pages)} pages, {len(crawl.forms)} forms, {len(crawl.api_endpoints)} API endpoints.")

    log("endpoint_analysis_agent", "Analyzing endpoints and parameters...")
    log("vulnerability_detection_agent", "Running vulnerability tests...")
    raw_findings = await run_scan(crawl, max_targets=30, concurrency=5, timeout=10.0)
    log("vulnerability_detection_agent", f"Found {len(raw_findings)} potential issues.")

    log("exploit_validation_agent", "Validating and justifying findings...")
    vulnerabilities = validate_findings(raw_findings)
    score = compute_security_posture_score(vulnerabilities, num_endpoints=len(crawl.pages))
    for i, v in enumerate(vulnerabilities):
        v["id"] = v.get("id") or f"{scan_id}_{i}"

    attack_paths = []
    for v in vulnerabilities[:10]:
        attack_paths.append({
            "title": v.get("title", "Finding"),
            "nodes": [
                {"id": "entry", "label": "Target", "type": "entry"},
                {"id": "vuln", "label": v.get("parameter", "Parameter"), "type": "vulnerability"},
                {"id": "impact", "label": v.get("impact", "Impact"), "type": "impact"},
            ],
            "edges": [{"source": "entry", "target": "vuln"}, {"source": "vuln", "target": "impact"}],
        })

    log("risk_agent", "Computing security posture score...")
    summary = generate_report_summary(target_url, vulnerabilities, score, len(crawl.pages), scan_id)
    log("report_agent", "Generating report...")
    report_json = generate_report_json(
        scan_id, target_url, vulnerabilities, attack_paths, summary, [], crawl_data,
    )
    return {
        "scan_id": scan_id,
        "status": "completed",
        "security_posture_score": score,
        "vulnerabilities": vulnerabilities,
        "attack_paths": attack_paths,
        "summary": summary,
        "report_json": report_json,
        "crawl_data": crawl_data,
    }
