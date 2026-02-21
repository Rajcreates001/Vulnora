"""Base agent class for all security agents."""

from typing import Any, Dict

from db.supabase_client import store_agent_log
from db.redis_client import store_agent_output, broadcast_agent_chat


class BaseAgent:
    """Base class providing logging and state management for agents."""

    name: str = "base_agent"
    description: str = "Base agent"

    async def log(self, project_id: str, message: str, log_type: str = "info", data: Any = None) -> None:
        await store_agent_log(project_id, self.name, message, log_type, data)
        # Also broadcast to SSE for live agent chat
        await broadcast_agent_chat(project_id, self.name, message, log_type, data)

    async def save_output(self, project_id: str, output: Any) -> None:
        await store_agent_output(project_id, self.name, output)

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
