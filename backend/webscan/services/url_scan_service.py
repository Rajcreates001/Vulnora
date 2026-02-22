"""URL scan orchestration: safety, crawl, scan, analyze, report, persist."""

import asyncio
import re
import threading
import uuid
from typing import Any, Dict, List, Optional

from webscan.crawler.crawler import crawl_url, CrawlResult
from webscan.scanner.scanner import run_scan
from webscan.analyzer.analyzer import validate_findings, compute_security_posture_score
from webscan.report.report import generate_report_summary, generate_report_json

# Optional DB (sync Supabase client — run in executor)
try:
    from db.supabase_client import (
        create_url_scan as _db_create_url_scan,
        get_url_scan as _db_get_url_scan,
        update_url_scan as _db_update_url_scan,
    )
    _DB_AVAILABLE = True
except Exception:
    _DB_AVAILABLE = False
    _db_create_url_scan = _db_get_url_scan = _db_update_url_scan = None

# In-memory fallback when DB not configured
_url_scan_cache: Dict[str, Dict[str, Any]] = {}

# Safety
MAX_SCAN_DEPTH = 25
MAX_REQUESTS_PER_SCAN = 500
ALLOWED_DOMAIN_PATTERN = re.compile(
    r"^https?://([a-zA-Z0-9][-a-zA-Z0-9]*\.)*[a-zA-Z0-9][-a-zA-Z0-9]*(\.[a-zA-Z]{2,})?(:\d+)?",
    re.I,
)
BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "internal"}
DISCLAIMER = "Only scan systems you own or have permission to test."


def validate_url_allowed(url: str) -> tuple[bool, str]:
    """Validate URL is allowed for scanning. Returns (ok, error_message)."""
    if not url or not url.strip():
        return False, "URL is required."
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        return False, "URL must use http or https."
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if host in BLOCKED_HOSTS and not _allow_localhost():
            return False, "Scanning localhost is disabled in this environment."
        if not ALLOWED_DOMAIN_PATTERN.match(url):
            return False, "URL format is invalid."
    except Exception as e:
        return False, str(e)
    return True, ""


def _allow_localhost() -> bool:
    import os
    return os.environ.get("VERDEXA_ALLOW_LOCALHOST_SCAN", "").lower() in ("1", "true", "yes")


def _gen_scan_id() -> str:
    return str(uuid.uuid4())


async def _run_scan_async(
    scan_id: str,
    target_url: str,
    credentials: Optional[Dict[str, str]] = None,
) -> None:
    """Background scan pipeline: crawl -> scan -> analyze -> report."""
    def log(msg: str, agent: str = "url_scan"):
        _append_log(scan_id, {"agent_name": agent, "message": msg, "log_type": "info"})

    try:
        _set_status(scan_id, "crawling", "Crawling target and discovering endpoints...")
        crawl = await crawl_url(
            target_url,
            max_pages=MAX_SCAN_DEPTH,
            use_playwright=bool(credentials),
            credentials=credentials,
            timeout=15.0,
        )
        crawl_data = crawl.to_dict()
        _set_crawl_data(scan_id, crawl_data)
        log(f"Crawled {len(crawl.pages)} pages, {len(crawl.forms)} forms, {len(crawl.api_endpoints)} API endpoints.")

        _set_status(scan_id, "scanning", "Running vulnerability tests...")
        raw_findings = await run_scan(crawl, max_targets=30, concurrency=5, timeout=10.0)
        log(f"Scanner reported {len(raw_findings)} potential findings.")

        _set_status(scan_id, "analyzing", "Validating and scoring findings...")
        vulnerabilities = validate_findings(raw_findings)
        for i, v in enumerate(vulnerabilities):
            v["id"] = v.get("id") or f"{scan_id}_{i}"
        score = compute_security_posture_score(vulnerabilities, num_endpoints=len(crawl.pages))
        attack_paths = _build_attack_paths(vulnerabilities, crawl_data)
        summary = generate_report_summary(
            target_url, vulnerabilities, score, len(crawl.pages), scan_id,
        )
        report_json = generate_report_json(
            scan_id, target_url, vulnerabilities, attack_paths, summary,
            _get_logs(scan_id), crawl_data,
        )
        _set_status(scan_id, "completed", "Scan complete.")
        _set_result(scan_id, {
            "security_posture_score": score,
            "vulnerabilities": vulnerabilities,
            "attack_paths": attack_paths,
            "summary": summary,
            "report_json": report_json,
        })
    except Exception as e:
        _set_status(scan_id, "failed", str(e))
        _set_result(scan_id, {"error_message": str(e)})


def _build_attack_paths(vulnerabilities: List[Dict], crawl_data: Dict) -> List[Dict]:
    """Simple attack path: entry -> vuln -> impact."""
    paths = []
    for v in vulnerabilities[:10]:
        paths.append({
            "title": v.get("title", "Finding"),
            "nodes": [
                {"id": "entry", "label": "Target", "type": "entry"},
                {"id": "vuln", "label": v.get("parameter", "Parameter"), "type": "vulnerability"},
                {"id": "impact", "label": v.get("impact", "Impact"), "type": "impact"},
            ],
            "edges": [
                {"source": "entry", "target": "vuln"},
                {"source": "vuln", "target": "impact"},
            ],
        })
    return paths


def _append_log(scan_id: str, entry: Dict[str, Any]) -> None:
    if _DB_AVAILABLE and _db_get_url_scan and _db_update_url_scan:
        try:
            rec = _url_scan_cache.get(scan_id) or _db_get_url_scan(scan_id) or {}
            logs = list(rec.get("agent_logs") or [])
            logs.append(entry)
            _db_update_url_scan(scan_id, {"agent_logs": logs})
        except Exception:
            pass
    if scan_id in _url_scan_cache:
        logs = _url_scan_cache[scan_id].setdefault("agent_logs", [])
        logs.append(entry)


def _get_logs(scan_id: str) -> List[Dict]:
    rec = _url_scan_cache.get(scan_id)
    if rec:
        return rec.get("agent_logs") or []
    if _DB_AVAILABLE and _db_get_url_scan:
        try:
            r = _db_get_url_scan(scan_id)
            return r.get("agent_logs") or [] if r else []
        except Exception:
            pass
    return []


def _set_status(scan_id: str, status: str, message: str = "") -> None:
    if _DB_AVAILABLE and _db_update_url_scan:
        try:
            _db_update_url_scan(scan_id, {"status": status, "error_message": message or None})
        except Exception:
            pass
    if scan_id in _url_scan_cache:
        _url_scan_cache[scan_id]["status"] = status
        if message:
            _url_scan_cache[scan_id]["error_message"] = message


def _set_crawl_data(scan_id: str, data: Dict) -> None:
    if _DB_AVAILABLE and _db_update_url_scan:
        try:
            _db_update_url_scan(scan_id, {"crawl_data": data})
        except Exception:
            pass
    if scan_id in _url_scan_cache:
        _url_scan_cache[scan_id]["crawl_data"] = data


def _set_result(scan_id: str, data: Dict) -> None:
    if _DB_AVAILABLE and _db_update_url_scan:
        try:
            _db_update_url_scan(scan_id, data)
        except Exception:
            pass
    if scan_id in _url_scan_cache:
        _url_scan_cache[scan_id].update(data)


def _run_in_thread(scan_id: str, target_url: str, credentials: Optional[Dict[str, str]]) -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run_scan_async(scan_id, target_url, credentials))
    finally:
        loop.close()


async def start_url_scan(
    target_url: str,
    credentials: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Validate URL, create scan record, start background scan. Returns scan_id and status."""
    ok, err = validate_url_allowed(target_url)
    if not ok:
        raise ValueError(err)
    scan_id = _gen_scan_id()
    if _DB_AVAILABLE and _db_create_url_scan:
        try:
            row = await _db_create_url_scan(target_url)
            scan_id = row.get("id", scan_id)
        except Exception:
            pass
    _url_scan_cache[scan_id] = {
        "id": scan_id,
        "target_url": target_url,
        "status": "pending",
        "security_posture_score": 0,
        "crawl_data": {},
        "vulnerabilities": [],
        "attack_paths": [],
        "summary": {},
        "agent_logs": [],
        "report_json": {},
    }
    thread = threading.Thread(target=_run_in_thread, args=(scan_id, target_url, credentials))
    thread.daemon = True
    thread.start()
    return {
        "scan_id": scan_id,
        "target_url": target_url,
        "status": "pending",
        "message": "URL scan started. Poll /api/url-results/{scan_id} for results.",
        "disclaimer": DISCLAIMER,
    }


async def get_url_scan_status(scan_id: str) -> Dict[str, Any]:
    """Return current status for a scan."""
    rec = _url_scan_cache.get(scan_id)
    if rec:
        return {
            "scan_id": scan_id,
            "status": rec.get("status", "pending"),
            "target_url": rec.get("target_url", ""),
            "security_posture_score": rec.get("security_posture_score", 0),
        }
    if _DB_AVAILABLE and _db_get_url_scan:
        try:
            r = await _db_get_url_scan(scan_id)
            if r:
                return {
                    "scan_id": r.get("id", scan_id),
                    "status": r.get("status", "pending"),
                    "target_url": r.get("target_url", ""),
                    "security_posture_score": r.get("security_posture_score", 0),
                }
        except Exception:
            pass
    return {"scan_id": scan_id, "status": "unknown", "target_url": "", "security_posture_score": 0}


async def get_url_scan_results(scan_id: str) -> Dict[str, Any]:
    """Full results in standardized format."""
    rec = _url_scan_cache.get(scan_id)
    if not rec and _DB_AVAILABLE and _db_get_url_scan:
        try:
            rec = await _db_get_url_scan(scan_id)
        except Exception:
            rec = None
    if not rec:
        return {
            "scan_id": scan_id,
            "target_url": "",
            "security_posture_score": 0,
            "vulnerabilities": [],
            "attack_paths": [],
            "summary": {},
            "agent_logs": [],
            "status": "unknown",
        }
    report = rec.get("report_json") or {}
    if report:
        report["status"] = rec.get("status", "completed")
        return report
    return {
        "scan_id": rec.get("id", scan_id),
        "target_url": rec.get("target_url", ""),
        "security_posture_score": rec.get("security_posture_score", 0),
        "vulnerabilities": rec.get("vulnerabilities", []),
        "attack_paths": rec.get("attack_paths", []),
        "summary": rec.get("summary", {}),
        "agent_logs": rec.get("agent_logs", []),
        "discovered_endpoints": {"pages": (rec.get("crawl_data") or {}).get("pages", []), "forms": (rec.get("crawl_data") or {}).get("forms", []), "api_endpoints": (rec.get("crawl_data") or {}).get("api_endpoints", [])},
        "status": rec.get("status", "completed"),
    }
