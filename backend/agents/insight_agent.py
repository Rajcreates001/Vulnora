"""Insight Agent — Provides human-level insights and context for each vulnerability."""

from agents.base_agent import BaseAgent
from utils.llm_client import get_llm_response
from db.redis_client import update_scan_progress
from typing import Any, Dict, List

SYSTEM_PROMPT = """You are a senior security analyst. For each vulnerability, provide:
- Why it was missed by automated tools or previous agents (if applicable)
- Human-level context: how a real attacker would exploit it, and why it matters in this codebase
- Suggestions for reducing alert fatigue (e.g., grouping, deduplication, prioritization)
- Output valid JSON:
{
  "insights": [
    {
      "title": "...",
      "why_missed": "...",
      "attacker_context": "...",
      "alert_fatigue_reduction": "..."
    }
  ]
}
"""

class InsightAgent(BaseAgent):
    name = "insight_agent"
    description = "Provides human-level insights and alert fatigue reduction"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        project_id = state["project_id"]
        vulns = state.get("vulnerabilities", [])
        await self.log(project_id, "Generating human-level insights for vulnerabilities")
        await update_scan_progress(project_id, "analysis", self.name, 0.1, "Generating insights and alert reduction...")

        insights = []
        for v in vulns:
            user_prompt = f"""For the following vulnerability, provide:
- Why it might be missed by tools/agents
- Attacker context (how/why it matters)
- Suggestions to reduce alert fatigue

VULNERABILITY:
{v}
"""
            try:
                response = await get_llm_response(SYSTEM_PROMPT, user_prompt, json_mode=True, max_tokens=1024)
                result = response if isinstance(response, dict) else None
                if not result:
                    import json
                    result = json.loads(response)
                if "insights" in result:
                    insights.extend(result["insights"])
                else:
                    insights.append(result)
            except Exception as e:
                await self.log(project_id, f"Insight generation failed: {str(e)}", "warning")
                insights.append({
                    "title": v.get("title", ""),
                    "why_missed": "Could not generate insight.",
                    "attacker_context": "N/A",
                    "alert_fatigue_reduction": "N/A"
                })

        state["insights"] = insights
        await self.save_output(project_id, {"insights": insights})
        await self.log(project_id, f"Insight generation complete: {len(insights)} insights", "success")
        await update_scan_progress(project_id, "analysis", self.name, 1.0, "Insight agent complete")
        return state
