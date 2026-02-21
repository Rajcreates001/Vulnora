"""Scan and results API routes."""

import asyncio
import json

from fastapi import APIRouter, HTTPException, Depends, Request
from utils import verify_jwt_token, verify_api_key
from fastapi.responses import StreamingResponse

from services.scan_service import start_scan, get_scan_status
from db.supabase_client import get_vulnerabilities, get_vulnerability, get_agent_logs
from db.redis_client import get_agent_output, subscribe_sse, unsubscribe_sse
from models.schemas import APIResponse

router = APIRouter(prefix="/api", tags=["scanning"])


@router.post("/start-scan")
async def start_security_scan(
    request: dict,
    jwt_payload: dict = Depends(verify_jwt_token),
    api_key_ok: bool = Depends(verify_api_key),
):
    """Start a security scan for a project."""
    project_id = request.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id is required")

    force = request.get("force", False)

    try:
        result = await start_scan(project_id, force=force)
        return APIResponse(success=True, data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scan-status/{project_id}")
async def scan_status(
    project_id: str,
    jwt_payload: dict = Depends(verify_jwt_token),
    api_key_ok: bool = Depends(verify_api_key),
):
    """Get current scan status."""
    try:
        status = await get_scan_status(project_id)
        return APIResponse(success=True, data=status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/results/{project_id}")
async def get_results(
    project_id: str,
    jwt_payload: dict = Depends(verify_jwt_token),
    api_key_ok: bool = Depends(verify_api_key),
):
    """Get scan results for a project."""
    vulns = await get_vulnerabilities(project_id)

    severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for v in vulns:
        sev = v.get("severity", "Medium")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    # Get report from cache
    report = await get_agent_output(project_id, "report_generation_agent")

    # Get attack paths from exploit data
    exploit_data = await get_agent_output(project_id, "exploit_simulation_agent")
    attack_paths = []
    if exploit_data and isinstance(exploit_data, dict):
        for exploit in exploit_data.get("exploits", []):
            ap = exploit.get("attack_path", [])
            if ap:
                nodes = []
                edges = []
                for idx, step in enumerate(ap):
                    node_id = f"node_{idx}"
                    nodes.append({
                        "id": node_id,
                        "label": step.get("node", f"Step {idx+1}"),
                        "node_type": step.get("type", "function"),
                        "data": {"description": step.get("description", "")},
                    })
                    if idx > 0:
                        edges.append({
                            "id": f"edge_{idx-1}_{idx}",
                            "source": f"node_{idx-1}",
                            "target": node_id,
                            "label": "",
                        })
                attack_paths.append({
                    "vulnerability": exploit.get("vulnerability_title", ""),
                    "nodes": nodes,
                    "edges": edges,
                })

    return APIResponse(success=True, data={
        "project_id": project_id,
        "vulnerabilities": vulns,
        "total": len(vulns),
        "critical_count": severity_counts["Critical"],
        "high_count": severity_counts["High"],
        "medium_count": severity_counts["Medium"],
        "low_count": severity_counts["Low"],
        "report": report,
        "attack_paths": attack_paths,
    })


@router.get("/vulnerabilities/{vuln_id}")
async def get_vulnerability_detail(
    vuln_id: str,
    jwt_payload: dict = Depends(verify_jwt_token),
    api_key_ok: bool = Depends(verify_api_key),
):
    """Get vulnerability details."""
    vuln = await get_vulnerability(vuln_id)
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    return APIResponse(success=True, data=vuln)


@router.get("/agent-logs/{project_id}")
async def get_project_agent_logs(
    project_id: str,
    jwt_payload: dict = Depends(verify_jwt_token),
    api_key_ok: bool = Depends(verify_api_key),
):
    """Get agent logs for a project."""
    logs = await get_agent_logs(project_id)
    return APIResponse(success=True, data={"logs": logs, "total": len(logs)})


@router.get("/scan-stream/{project_id}")
async def scan_event_stream(
    project_id: str,
    jwt_payload: dict = Depends(verify_jwt_token),
    api_key_ok: bool = Depends(verify_api_key),
):
    """Server-Sent Events stream for live agent chat and scan progress."""

    async def event_generator():
        q = subscribe_sse(project_id)
        try:
            # Send initial ping
            yield f"data: {json.dumps({'type': 'connected', 'message': 'Stream connected'})}\n\n"

            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield f"data: {json.dumps(event, default=str)}\n\n"

                    # Stop streaming when scan completes
                    if event.get("type") == "progress" and event.get("status") in ("completed", "failed"):
                        yield f"data: {json.dumps({'type': 'done', 'message': 'Scan finished'})}\n\n"
                        break
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f"data: {json.dumps({'type': 'ping'})}\n\n"
        finally:
            unsubscribe_sse(project_id, q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/report/{project_id}")
async def get_report(
    project_id: str,
    jwt_payload: dict = Depends(verify_jwt_token),
    api_key_ok: bool = Depends(verify_api_key),
):
    """Get the detailed security report for a project."""
    report = await get_agent_output(project_id, "report_generation_agent")
    if not report:
        # Fallback: build from vulnerabilities
        vulns = await get_vulnerabilities(project_id)
        if not vulns:
            return APIResponse(success=True, data={"report": None, "message": "No scan results available"})

        severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for v in vulns:
            sev = v.get("severity", "Medium")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        total = len(vulns)
        if severity_counts["Critical"] > 0:
            rating = "Critical"
        elif severity_counts["High"] > 0:
            rating = "High"
        elif severity_counts["Medium"] > 0:
            rating = "Medium"
        else:
            rating = "Low"

        report = {
            "executive_summary": f"Security assessment identified {total} vulnerabilities.",
            "total_vulnerabilities": total,
            "critical_count": severity_counts["Critical"],
            "high_count": severity_counts["High"],
            "medium_count": severity_counts["Medium"],
            "low_count": severity_counts["Low"],
            "overall_risk_rating": rating,
            "key_findings": [v.get("title", "") for v in vulns[:5]],
            "recommendations": ["Address all critical vulnerabilities immediately"],
            "conclusion": f"The application needs security improvements. {severity_counts['Critical'] + severity_counts['High']} high-priority issues require remediation.",
        }

    # Also get debate results for reasoning
    debate_data = await get_agent_output(project_id, "security_debate_agent")

    return APIResponse(success=True, data={
        "report": report,
        "debate_results": debate_data.get("debates", []) if debate_data else [],
    })
