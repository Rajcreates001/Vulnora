# Verdexa URL / Website Security Scan

This module adds **dynamic website security scanning** (URL-based) to Verdexa without changing existing repository/code scan flows.

## Capabilities

- **Crawler**: Discovers pages, forms, inputs, and API-like endpoints (httpx + optional Playwright for JS).
- **Scanner**: Deterministic payload injection for SQLi, XSS, path traversal, open redirect.
- **Analyzer**: Exploit validation with structured justification, impact, and "why missed" reasoning.
- **Report**: Security posture score (0–100), attack paths, JSON report.

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/api/scan/url` | Start scan (body: `{ "url": "https://..." }`) |
| POST   | `/api/scan/url-with-auth` | Start scan with optional `credentials: { username, password }` |
| GET    | `/api/url-scan-status/{scan_id}` | Poll status |
| GET    | `/api/url-results/{scan_id}` | Full results (vulnerabilities, attack_paths, summary, agent_logs) |
| GET    | `/api/url-vulnerabilities/{vuln_id}` | Single vulnerability (vuln_id = `scan_id_index`) |

## Safety

- URL validation (http/https, blocked hosts like localhost unless `VERDEXA_ALLOW_LOCALHOST_SCAN=1`).
- Max crawl depth and request limits in `url_scan_service.py`.
- Disclaimer: *Only scan systems you own or have permission to test.*

## Database

Run the new schema in Supabase (see `db/schema.sql`):

- `url_scans`: scan id, target_url, status, security_posture_score, crawl_data, vulnerabilities, attack_paths, summary, agent_logs, report_json.
- `url_scan_vulnerabilities`: optional normalized table (currently results live in `url_scans.vulnerabilities` JSONB).

If the DB is not configured or tables are missing, scans still run and results are kept in memory (per process).

## Deployment

- **Backend (Render)**: Include Playwright in `requirements.txt`. In Dockerfile, `playwright install chromium` is optional; if it fails, the crawler uses httpx-only (no JS rendering).
- **Frontend (Vercel)**: No extra config. Dashboard has a "Website Security Scan" card; results live at `/webscan/[scanId]`.

## Structure

```
webscan/
  crawler/     # crawl_url(), CrawlResult
  scanner/     # run_scan(), payload injection
  payloads/    # SQLi, XSS, path traversal, etc.
  analyzer/    # validate_findings(), why_missed, security_posture_score
  report/      # generate_report_json(), summary
  services/    # url_scan_service: start_url_scan, get_url_scan_status, get_url_scan_results
  workflow.py  # Optional LangGraph-style pipeline (crawler -> scan -> validate -> report)
```

Existing **repository scanning** (SAST, agents, report) is unchanged and remains under `graph/workflow.py`, `routes/scanning.py`, and the dashboard "Code Security" tab.
