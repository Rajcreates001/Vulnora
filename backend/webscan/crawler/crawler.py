"""Crawler: fetch target URL, extract links, forms, inputs, and API-like endpoints."""

import asyncio
import re
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

# Optional Playwright for JS-rendered pages
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class CrawlResult:
    """Structured crawl output for the scanner."""

    def __init__(
        self,
        target_url: str,
        pages: List[Dict[str, Any]],
        forms: List[Dict[str, Any]],
        inputs: List[Dict[str, Any]],
        api_endpoints: List[Dict[str, Any]],
        cookies: Optional[Dict[str, str]] = None,
    ):
        self.target_url = target_url
        self.pages = pages
        self.forms = forms
        self.inputs = inputs
        self.api_endpoints = api_endpoints
        self.cookies = cookies or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pages": self.pages,
            "forms": self.forms,
            "inputs": self.inputs,
            "api_endpoints": self.api_endpoints,
            "cookies": self.cookies,
        }


def _normalize_url(base: str, href: str) -> Optional[str]:
    if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
        return None
    try:
        u = urljoin(base, href)
        parsed = urlparse(u)
        if parsed.scheme not in ("http", "https"):
            return None
        return u
    except Exception:
        return None


def _same_origin(base: str, url: str) -> bool:
    try:
        return urlparse(base).netloc == urlparse(url).netloc
    except Exception:
        return False


def _extract_forms(soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
    forms = []
    for form in soup.find_all("form"):
        action = form.get("action") or page_url
        method = (form.get("method") or "GET").upper()
        action_url = urljoin(page_url, action)
        inputs_list = []
        for inp in form.find_all(["input", "textarea"]):
            name = inp.get("name")
            if not name:
                continue
            inputs_list.append({
                "name": name,
                "type": inp.get("type", "text"),
                "value": inp.get("value", ""),
            })
        forms.append({
            "action": action_url,
            "method": method,
            "inputs": inputs_list,
        })
    return forms


def _extract_inputs_from_page(soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
    inputs_list = []
    seen = set()
    for inp in soup.find_all(["input", "textarea"]):
        name = inp.get("name")
        if not name or name in seen:
            continue
        seen.add(name)
        inputs_list.append({
            "page": page_url,
            "name": name,
            "type": inp.get("type", "text"),
        })
    return inputs_list


def _extract_links(soup: BeautifulSoup, page_url: str) -> List[str]:
    links = []
    for a in soup.find_all("a", href=True):
        u = _normalize_url(page_url, a["href"])
        if u and _same_origin(page_url, u):
            links.append(u)
    for tag in soup.find_all(["script", "img"], src=True):
        u = _normalize_url(page_url, tag["src"])
        if u and _same_origin(page_url, u):
            links.append(u)
    return list(dict.fromkeys(links))


def _guess_api_endpoints(links: List[str], base_url: str) -> List[Dict[str, Any]]:
    api_patterns = re.compile(
        r"/api/|/v1/|/v2/|/graphql|/rest/|/json/|\.json\b|/webhook",
        re.I
    )
    endpoints = []
    seen = set()
    for link in links:
        if link in seen:
            continue
        if api_patterns.search(link):
            seen.add(link)
            parsed = urlparse(link)
            qs = parsed.query
            params = []
            if qs:
                from urllib.parse import parse_qs
                for k in parse_qs(qs).keys():
                    params.append({"name": k, "sample": ""})
            endpoints.append({
                "url": link,
                "method": "GET",
                "parameters": params,
            })
    return endpoints


async def _fetch_with_httpx(
    client: httpx.AsyncClient,
    url: str,
    method: str = "GET",
    data: Optional[Dict[str, str]] = None,
    timeout: float = 15.0,
) -> tuple[int, str, Dict[str, str]]:
    try:
        if method.upper() == "GET":
            r = await client.get(url, timeout=timeout)
        else:
            r = await client.post(url, data=data or {}, timeout=timeout)
        return r.status_code, r.text, dict(r.headers)
    except Exception as e:
        return 0, str(e), {}


async def _crawl_with_httpx(
    target_url: str,
    max_pages: int = 25,
    timeout: float = 15.0,
) -> CrawlResult:
    base_parsed = urlparse(target_url)
    base_origin = f"{base_parsed.scheme}://{base_parsed.netloc}"
    seen: Set[str] = set()
    to_visit: List[str] = [target_url]
    all_pages: List[Dict[str, Any]] = []
    all_forms: List[Dict[str, Any]] = []
    all_inputs: List[Dict[str, Any]] = []
    all_api: List[Dict[str, Any]] = []
    all_links: List[str] = []

    async with httpx.AsyncClient(
        follow_redirects=True,
        headers={"User-Agent": "Verdexa-Scanner/1.0"},
    ) as client:
        while to_visit and len(seen) < max_pages:
            url = to_visit.pop(0)
            if url in seen:
                continue
            seen.add(url)
            status, body, headers = await _fetch_with_httpx(client, url, timeout=timeout)
            all_pages.append({"url": url, "status": status})
            try:
                soup = BeautifulSoup(body, "html.parser")
            except Exception:
                soup = BeautifulSoup("", "html.parser")

            forms = _extract_forms(soup, url)
            all_forms.extend(forms)
            all_inputs.extend(_extract_inputs_from_page(soup, url))
            links = _extract_links(soup, url)
            all_links.extend(links)
            for link in links:
                if link not in seen and _same_origin(target_url, link):
                    to_visit.append(link)

            await asyncio.sleep(0.3)

    api_endpoints = _guess_api_endpoints(list(dict.fromkeys(all_links)), target_url)
    all_api.extend(api_endpoints)
    return CrawlResult(
        target_url=target_url,
        pages=all_pages,
        forms=all_forms,
        inputs=all_inputs,
        api_endpoints=all_api,
    )


async def _crawl_with_playwright(
    target_url: str,
    max_pages: int = 25,
    timeout: float = 15000,
    credentials: Optional[Dict[str, str]] = None,
) -> CrawlResult:
    if not PLAYWRIGHT_AVAILABLE:
        return await _crawl_with_httpx(target_url, max_pages=max_pages, timeout=timeout / 1000.0)

    base_parsed = urlparse(target_url)
    base_origin = f"{base_parsed.scheme}://{base_parsed.netloc}"
    seen: Set[str] = set()
    to_visit: List[str] = [target_url]
    all_pages = []
    all_forms = []
    all_inputs = []
    all_links: List[str] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Verdexa-Scanner/1.0",
            ignore_https_errors=True,
        )
        if credentials:
            await context.add_init_script("""
                window.__verdexa_login = true;
            """)
        page = await context.new_page()
        page.set_default_timeout(timeout)

        try:
            await page.goto(target_url, wait_until="networkidle")
            if credentials:
                try:
                    await page.fill('input[type="text"], input[name="username"], input[name="email"]', credentials.get("username", ""))
                    await page.fill('input[type="password"]', credentials.get("password", ""))
                    await page.click('button[type="submit"], input[type="submit"]')
                    await page.wait_for_load_state("networkidle")
                except Exception:
                    pass
        except Exception:
            pass

        while to_visit and len(seen) < max_pages:
            url = to_visit.pop(0)
            if url in seen:
                continue
            seen.add(url)
            try:
                resp = await page.goto(url, wait_until="domcontentloaded")
                status = resp.status if resp else 0
            except Exception:
                status = 0
            all_pages.append({"url": url, "status": status})
            try:
                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")
            except Exception:
                soup = BeautifulSoup("", "html.parser")
            forms = _extract_forms(soup, url)
            all_forms.extend(forms)
            all_inputs.extend(_extract_inputs_from_page(soup, url))
            links = _extract_links(soup, url)
            all_links.extend(links)
            for link in links:
                if link not in seen and _same_origin(target_url, link):
                    to_visit.append(link)
            await asyncio.sleep(0.2)

        await context.close()
        await browser.close()

    api_endpoints = _guess_api_endpoints(list(dict.fromkeys(all_links)), target_url)
    return CrawlResult(
        target_url=target_url,
        pages=all_pages,
        forms=all_forms,
        inputs=all_inputs,
        api_endpoints=api_endpoints,
    )


async def crawl_url(
    target_url: str,
    max_pages: int = 25,
    use_playwright: bool = True,
    credentials: Optional[Dict[str, str]] = None,
    timeout: float = 15.0,
) -> CrawlResult:
    """Crawl target URL; use Playwright if available and requested, else httpx."""
    if use_playwright and PLAYWRIGHT_AVAILABLE and credentials:
        return await _crawl_with_playwright(
            target_url,
            max_pages=max_pages,
            timeout=timeout * 1000,
            credentials=credentials,
        )
    return await _crawl_with_httpx(target_url, max_pages=max_pages, timeout=timeout)
