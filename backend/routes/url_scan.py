"""URL / Website security scan API routes."""

from fastapi import APIRouter, HTTPException, Depends, Body

from utils import verify_jwt_token, verify_api_key
from models.schemas import APIResponse
from webscan.services.url_scan_service import (
    start_url_scan,
    get_url_scan_status,
    get_url_scan_results,
    validate_url_allowed,
)

router = APIRouter(prefix="/api", tags=["url-scan"])


@router.post("/scan/url")
async def scan_url(
    body: dict = Body(...),
    jwt_payload: dict = Depends(verify_jwt_token),
    api_key_ok: bool = Depends(verify_api_key),
):
    """Start a website security scan (no auth)."""
    url = body.get("url", "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="url is required")
    ok, err = validate_url_allowed(url)
    if not ok:
        raise HTTPException(status_code=400, detail=err)
    try:
        result = await start_url_scan(target_url=url, credentials=None)
        return APIResponse(success=True, data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan/url-with-auth")
async def scan_url_with_auth(
    body: dict = Body(...),
    jwt_payload: dict = Depends(verify_jwt_token),
    api_key_ok: bool = Depends(verify_api_key),
):
    """Start a website security scan with optional login credentials."""
    url = body.get("url", "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="url is required")
    credentials = body.get("credentials") or {}
    if not isinstance(credentials, dict):
        credentials = {}
    ok, err = validate_url_allowed(url)
    if not ok:
        raise HTTPException(status_code=400, detail=err)
    creds = None
    if credentials.get("username") or credentials.get("password"):
        creds = {
            "username": credentials.get("username", ""),
            "password": credentials.get("password", ""),
        }
    try:
        result = await start_url_scan(target_url=url, credentials=creds)
        return APIResponse(success=True, data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/url-results/{scan_id}")
async def url_results(
    scan_id: str,
    jwt_payload: dict = Depends(verify_jwt_token),
    api_key_ok: bool = Depends(verify_api_key),
):
    """Get full URL scan results (standardized format)."""
    try:
        data = await get_url_scan_results(scan_id)
        return APIResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/url-scan-status/{scan_id}")
async def url_scan_status(
    scan_id: str,
    jwt_payload: dict = Depends(verify_jwt_token),
    api_key_ok: bool = Depends(verify_api_key),
):
    """Get URL scan status (for polling)."""
    try:
        data = await get_url_scan_status(scan_id)
        return APIResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/url-vulnerabilities/{vuln_id}")
async def url_vulnerability_detail(
    vuln_id: str,
    jwt_payload: dict = Depends(verify_jwt_token),
    api_key_ok: bool = Depends(verify_api_key),
):
    """Get a single URL scan vulnerability by id (format: scan_id_index or stored id)."""
    try:
        if "_" in vuln_id:
            scan_id, idx_str = vuln_id.rsplit("_", 1)
            if idx_str.isdigit():
                results = await get_url_scan_results(scan_id)
                vulns = results.get("vulnerabilities", [])
                idx = int(idx_str)
                if 0 <= idx < len(vulns):
                    return APIResponse(success=True, data=vulns[idx])
        results = await get_url_scan_results(vuln_id)
        vulns = results.get("vulnerabilities", [])
        for v in vulns:
            if v.get("id") == vuln_id:
                return APIResponse(success=True, data=v)
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
