"""Run payload injection against endpoints/forms and detect anomalies."""

import asyncio
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import httpx

from webscan.payloads.payloads import (
    get_payloads_for_category,
    SQLI_PAYLOADS,
    XSS_PAYLOADS,
    PATH_TRAVERSAL_PAYLOADS,
    OPEN_REDIRECT_PAYLOADS,
    SENSITIVE_PATHS,
)
from webscan.crawler.crawler import CrawlResult


class ScanTarget:
    """Single target: URL + method + parameters."""

    def __init__(
        self,
        url: str,
        method: str = "GET",
        params: Optional[List[Dict[str, str]]] = None,
        body: Optional[Dict[str, str]] = None,
    ):
        self.url = url
        self.method = method.upper()
        self.params = params or []
        self.body = body or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "method": self.method,
            "params": self.params,
            "body": self.body,
        }


# Patterns that suggest vulnerability (deterministic signals)
SQL_ERROR_PATTERNS = re.compile(
    r"(sql (syntax|error|exception)|mysql_|postgresql|ora-\d+|syntax error.*sql|unclosed quotation)",
    re.I,
)
XSS_REFLECTION_PATTERNS = re.compile(
    r"<script|alert\s*\(|onerror\s*=",
    re.I,
)
PATH_TRAVERSAL_PATTERNS = re.compile(
    r"root:.*:0:0:|/etc/passwd|\\\\windows\\\\system32",
    re.I,
)


def _build_targets_from_crawl(crawl: CrawlResult) -> List[ScanTarget]:
    targets: List[ScanTarget] = []
    seen: set = set()

    for form in crawl.forms:
        key = (form["action"], form["method"])
        if key in seen:
            continue
        seen.add(key)
        params = [{"name": i["name"], "sample": i.get("value", "")} for i in form.get("inputs", [])]
        targets.append(ScanTarget(url=form["action"], method=form["method"], params=params))

    for ep in crawl.api_endpoints:
        url = ep.get("url", "")
        if not url:
            continue
        key = (url, ep.get("method", "GET"))
        if key in seen:
            continue
        seen.add(key)
        targets.append(ScanTarget(
            url=url,
            method=ep.get("method", "GET"),
            params=ep.get("parameters", []),
        ))

    for page in crawl.pages[:10]:
        u = page.get("url", "")
        if u and (u, "GET") not in seen:
            seen.add((u, "GET"))
            parsed = urlparse(u)
            params = [{"name": k, "sample": v[0] if v else ""} for k, v in parse_qs(parsed.query).items()]
            targets.append(ScanTarget(url=u, method="GET", params=params))

    return targets


async def _probe(
    client: httpx.AsyncClient,
    target: ScanTarget,
    param_name: str,
    payload: str,
    category: str,
    timeout: float = 10.0,
) -> Tuple[int, str, Dict[str, str], bool]:
    """Inject payload into param and return (status, body, headers, anomaly_detected)."""
    url = target.url
    if target.method == "GET":
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        qs[param_name] = [payload]
        new_query = urlencode(qs, doseq=True)
        url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
        try:
            r = await client.get(url, timeout=timeout)
        except Exception as e:
            return 0, str(e), {}, False
    else:
        data = {p["name"]: p.get("sample", "") for p in target.params}
        data[param_name] = payload
        try:
            r = await client.post(url, data=data, timeout=timeout)
        except Exception as e:
            return 0, str(e), {}, False

    body = r.text
    headers = dict(r.headers)
    anomaly = False
    if category == "sql_injection" and SQL_ERROR_PATTERNS.search(body):
        anomaly = True
    if category == "xss" and XSS_REFLECTION_PATTERNS.search(body):
        anomaly = True
    if category == "path_traversal" and PATH_TRAVERSAL_PATTERNS.search(body):
        anomaly = True
    if category == "open_redirect":
        loc = headers.get("location", "")
        if "evil.com" in loc or "javascript:" in loc:
            anomaly = True
    if not anomaly and category in ("sql_injection", "xss"):
        if r.status_code == 200 and len(body) != 0:
            anomaly = True
    return r.status_code, body, headers, anomaly


async def run_scan(
    crawl: CrawlResult,
    categories: Optional[List[str]] = None,
    max_targets: int = 30,
    concurrency: int = 5,
    timeout: float = 10.0,
) -> List[Dict[str, Any]]:
    """Run deterministic tests and return list of potential findings."""
    categories = categories or [
        "sql_injection",
        "xss",
        "path_traversal",
        "open_redirect",
    ]
    targets = _build_targets_from_crawl(crawl)[:max_targets]
    findings: List[Dict[str, Any]] = []
    sem = asyncio.Semaphore(concurrency)

    async def test_one(target: ScanTarget, param: Dict, payload: str, cat: str):
        async with sem:
            status, body, headers, anomaly = await _probe(
                client, target, param["name"], payload, cat, timeout=timeout
            )
            if anomaly or (cat == "sql_injection" and status == 200 and "error" in body.lower()):
                return {
                    "category": cat,
                    "url": target.url,
                    "method": target.method,
                    "parameter": param["name"],
                    "payload_used": payload,
                    "status_code": status,
                    "evidence_snippet": body[:500] if body else "",
                    "anomaly": anomaly,
                }
            return None

    async with httpx.AsyncClient(
        follow_redirects=False,
        headers={"User-Agent": "Verdexa-Scanner/1.0"},
    ) as client:
        tasks = []
        for target in targets:
            params = target.params or [{"name": "q", "sample": ""}]
            for param in params:
                name = param.get("name") or "q"
                for cat in categories:
                    payloads = get_payloads_for_category(cat)
                    for payload in payloads[:5]:
                        tasks.append(test_one(target, {"name": name, "sample": param.get("sample", "")}, payload, cat))
        results = await asyncio.gather(*tasks, return_exceptions=True)

    for r in results:
        if isinstance(r, dict) and r is not None:
            findings.append(r)
        if isinstance(r, Exception):
            pass
    return findings
