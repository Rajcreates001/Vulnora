"""Scan orchestration service."""

import asyncio
import sys
import traceback
from typing import Dict, Any, Optional

from graph.workflow import run_security_scan
from db.supabase_client import get_project, update_project, store_agent_log
from db.redis_client import get_scan_state, set_scan_state, broadcast_agent_chat


async def _run_scan_safe(project_id: str) -> None:
    """Run the scan and catch any exception to update status."""
    try:
        print(f"[SCAN] Starting scan for project {project_id}")
        sys.stdout.flush()
        result = await run_security_scan(project_id)
        print(f"[SCAN] Scan completed for project {project_id}")
        if result and result.get("error"):
            print(f"[SCAN] Scan had errors: {result.get('error')}")
        sys.stdout.flush()
    except Exception as e:
        error_msg = f"Scan crashed: {str(e)}\n{traceback.format_exc()}"
        print(f"CRITICAL ERROR: {error_msg}")
        sys.stderr.write(f"CRITICAL ERROR: {error_msg}\n")
        sys.stderr.flush()
        try:
            await update_project(project_id, {"scan_status": "failed"})
            await set_scan_state(project_id, {
                "status": "failed",
                "current_agent": "",
                "progress": 0,
                "agents_completed": [],
                "message": (str(e))[:500],
            })
            await store_agent_log(project_id, "system", f"Scan crashed: {str(e)}", "error")
            await broadcast_agent_chat(project_id, "system", f"Scan failed: {str(e)[:200]}", "error")
        except Exception as update_error:
            print(f"Failed to update failed status: {update_error}")


async def start_scan(project_id: str, force: bool = False) -> Dict[str, Any]:
    """Start a security scan as a background task in the same event loop."""
    project = await get_project(project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found")

    active_statuses = ("recon", "analysis", "exploit", "patch", "report", "scanning")
    if project.get("scan_status") in active_statuses and not force:
        raise ValueError("Scan already in progress")

    # Reset project status before starting
    await update_project(project_id, {"scan_status": "recon"})
    await set_scan_state(project_id, {
        "status": "recon",
        "current_agent": "recon_agent",
        "progress": 0,
        "agents_completed": [],
        "message": "Initializing security scan...",
    })

    # Run scan in same event loop so SSE broadcast and DB work correctly
    asyncio.create_task(_run_scan_safe(project_id))

    return {
        "project_id": project_id,
        "status": "recon",
        "current_agent": "recon_agent",
        "progress": 0,
        "agents_completed": [],
        "message": "Security scan started",
    }


async def get_scan_status(project_id: str) -> Dict[str, Any]:
    """Get current scan status from Redis."""
    # Check Redis for real-time status
    state = await get_scan_state(project_id)
    if state:
        return {
            "project_id": project_id,
            "status": state.get("status", "pending"),
            "current_agent": state.get("current_agent", ""),
            "progress": state.get("progress", 0),
            "agents_completed": state.get("agents_completed", []),
            "message": state.get("message", ""),
        }

    # Fallback to database
    project = await get_project(project_id)
    if project:
        return {
            "project_id": project_id,
            "status": project.get("scan_status", "pending"),
            "current_agent": "",
            "progress": 1.0 if project.get("scan_status") == "completed" else 0,
            "agents_completed": [],
            "message": "",
        }

    raise ValueError(f"Project {project_id} not found")
