"""Missed Vuln Reasoning Agent — Explains why vulnerabilities may have been missed by previous tools/agents."""

from agents.base_agent import BaseAgent
from utils.llm_client import get_llm_response
from db.redis_client import update_scan_progress
from typing import Any, Dict, List

SYSTEM_PROMPT = """You are a security expert. For each missed vulnerability, explain:
- Why it was missed by previous tools/agents (e.g., static analysis, LLM, heuristics)
- What could be improved in the detection pipeline
- Output valid JSON:
{
  "missed_reason": "...",
  "improvement": "..."
}
"""

class MissedVulnReasoningAgent(BaseAgent):
    name = "missed_vuln_reasoning_agent"
    description = "Explains why vulnerabilities may have been missed by previous tools/agents."

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        project_id = state["project_id"]
        missed = state.get("missed_vulnerabilities", [])
        await self.log(project_id, "Reasoning about missed vulnerabilities")
        await update_scan_progress(project_id, "analysis", self.name, 0.1, "Reasoning about missed vulnerabilities...")

        missed_reasons = []
        for v in missed:
            user_prompt = f"Why was the following vulnerability missed?\n{v}\n"
            try:
                response = await get_llm_response(SYSTEM_PROMPT, user_prompt, json_mode=True, max_tokens=512)
                result = response if isinstance(response, dict) else None
                if not result:
                    import json
                    result = json.loads(response)
                missed_reasons.append({
                    "vuln": v,
                    "reason": result.get("missed_reason", "N/A"),
                    "improvement": result.get("improvement", "N/A")
                })
            except Exception as e:
                # await self.log(project_id, f"Missed vuln reasoning failed: {str(e)}", "warning")
                missed_reasons.append({
                    "vuln": v,
                    "reason": "Could not generate reasoning.",
                    "improvement": "N/A"
                })

        state["missed_vuln_reasons"] = missed_reasons
        await self.save_output(project_id, {"missed_vuln_reasons": missed_reasons})
        await self.log(project_id, f"Missed vuln reasoning complete: {len(missed_reasons)}", "success")
        await update_scan_progress(project_id, "analysis", self.name, 1.0, "Missed vuln reasoning complete")
        return state
