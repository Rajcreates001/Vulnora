"""Scan orchestration service."""

import asyncio
from typing import Dict, Any, Optional

from graph.workflow import run_security_scan
from db.supabase_client import get_project, update_project
from db.redis_client import get_scan_state, set_scan_state


async def start_scan(project_id: str, force: bool = False) -> Dict[str, Any]:
    """Start a security scan as a background task."""
    project = await get_project(project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found")

    active_statuses = ("recon", "analysis", "exploit", "patch", "report", "scanning")
    if project.get("scan_status") in active_statuses and not force:
        raise ValueError("Scan already in progress")

    # Reset project status before starting
    await update_project(project_id, {"scan_status": "recon"})
    # Set initial scan state so polling works immediately
    await set_scan_state(project_id, {
        "status": "recon",
        "current_agent": "recon_agent",
        "progress": 0,
        "agents_completed": [],
        "message": "Initializing security scan...",
    })

    # Launch scan in background
    asyncio.create_task(run_security_scan(project_id))

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
