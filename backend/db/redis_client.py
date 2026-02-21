"""In-memory cache for agent memory and scan state (Redis-free fallback)."""

import json
import time
import asyncio
from typing import Any, Callable, Dict, List, Optional

# ─── In-Memory Store ──────────────────────────────────

_store: Dict[str, Any] = {}
_ttls: Dict[str, float] = {}

# SSE subscribers: project_id -> list of asyncio.Queue
_sse_subscribers: Dict[str, List[asyncio.Queue]] = {}


def _cleanup_expired():
    """Remove expired keys."""
    now = time.time()
    expired = [k for k, exp in _ttls.items() if exp < now]
    for k in expired:
        _store.pop(k, None)
        _ttls.pop(k, None)


async def set_cache(key: str, value: Any, ttl: int = 3600) -> None:
    _cleanup_expired()
    _store[key] = value
    _ttls[key] = time.time() + ttl


async def get_cache(key: str) -> Optional[Any]:
    _cleanup_expired()
    return _store.get(key)


async def delete_cache(key: str) -> None:
    _store.pop(key, None)
    _ttls.pop(key, None)


# ─── SSE Event Broadcasting ──────────────────────────

def subscribe_sse(project_id: str) -> asyncio.Queue:
    """Subscribe to live agent events for a project. Returns an asyncio.Queue."""
    if project_id not in _sse_subscribers:
        _sse_subscribers[project_id] = []
    q: asyncio.Queue = asyncio.Queue()
    _sse_subscribers[project_id].append(q)
    return q


def unsubscribe_sse(project_id: str, q: asyncio.Queue) -> None:
    """Remove a subscriber queue."""
    if project_id in _sse_subscribers:
        try:
            _sse_subscribers[project_id].remove(q)
        except ValueError:
            pass


async def _broadcast_event(project_id: str, event: Dict[str, Any]) -> None:
    """Push an event to all SSE subscribers for a project."""
    for q in _sse_subscribers.get(project_id, []):
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            pass


# ─── Scan State ───────────────────────────────────────

async def set_scan_state(project_id: str, state: Dict[str, Any]) -> None:
    await set_cache(f"scan:{project_id}", state, ttl=7200)


async def get_scan_state(project_id: str) -> Optional[Dict[str, Any]]:
    return await get_cache(f"scan:{project_id}")


async def update_scan_progress(
    project_id: str, status: str, agent: str, progress: float,
    message: str = "", mark_agent_completed: bool = False,
) -> None:
    state = await get_scan_state(project_id) or {}
    agents_completed = state.get("agents_completed", [])
    if agent and agent not in agents_completed and mark_agent_completed:
        agents_completed.append(agent)
    state.update({
        "status": status,
        "current_agent": agent,
        "progress": progress,
        "agents_completed": agents_completed,
        "message": message,
    })
    await set_scan_state(project_id, state)

    # Broadcast progress to SSE listeners
    await _broadcast_event(project_id, {
        "type": "progress",
        "agent": agent,
        "status": status,
        "progress": progress,
        "message": message,
        "agents_completed": agents_completed,
    })


# ─── Agent Memory ─────────────────────────────────────

async def store_agent_output(project_id: str, agent_name: str, output: Any) -> None:
    await set_cache(f"agent:{project_id}:{agent_name}", output, ttl=7200)


async def get_agent_output(project_id: str, agent_name: str) -> Optional[Any]:
    return await get_cache(f"agent:{project_id}:{agent_name}")


# ─── Live Agent Chat Broadcasting ─────────────────────

async def broadcast_agent_chat(
    project_id: str,
    agent_name: str,
    message: str,
    message_type: str = "info",
    data: Any = None,
) -> None:
    """Broadcast agent chat message to all SSE listeners."""
    await _broadcast_event(project_id, {
        "type": "agent_chat",
        "agent": agent_name,
        "message": message,
        "message_type": message_type,
        "data": data,
        "timestamp": time.time(),
    })
