"""Insight Agent — Provides human-level insights and context for vulnerabilities."""

import json
import asyncio
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
        # Process vulnerabilities in batches instead of one-by-one to avoid rate limits
        batch_size = 5
        for i in range(0, len(vulns), batch_size):
            batch = vulns[i:i + batch_size]
            progress = 0.1 + (0.8 * (i / max(len(vulns), 1)))
            await update_scan_progress(project_id, "analysis", self.name, progress, f"Generating insights batch {i // batch_size + 1}...")

            vuln_summaries = []
            for v in batch:
                vuln_summaries.append({
                    "title": v.get("title", "Unknown"),
                    "vulnerability_type": v.get("vulnerability_type", ""),
                    "severity": v.get("severity", "Medium"),
                    "file_path": v.get("file_path", ""),
                    "description": v.get("description", "")[:300],
                })

            user_prompt = f"""For each of the following vulnerabilities, provide insights:

VULNERABILITIES:
{json.dumps(vuln_summaries, indent=2)}
"""
            try:
                response = await get_llm_response(SYSTEM_PROMPT, user_prompt, json_mode=True, max_tokens=2048)
                result = json.loads(response)
                # The new schema is a direct array of insight objects
                if isinstance(result, list):
                    for insight in result:
                        # Find the original vulnerability by ID and update it
                        original_vuln = next((v for v in batch if v.get("id") == insight.get("id")), None)
                        if original_vuln:
                            original_vuln["cwe_id"] = insight.get("cwe_id")
                            original_vuln["cvss_vector"] = insight.get("cvss_vector")
                            if "impact" in insight:
                                original_vuln["impact"] = float(insight["impact"])
                            original_vuln["why_missed"] = insight.get("why_missed")
                            insights.append(original_vuln) # Add the updated vuln to the insights list
                        else:
                            insights.append(insight) # If original not found, add the insight as is
                else:
                    # await self.log(project_id, f"Insight batch {i // batch_size + 1} received unexpected JSON format: {response}", "warning")
                    # Fallback for unexpected format
                    for v in batch:
                        insights.append({
                            "id": v.get("id", "unknown_id"),
                            "cwe_id": "CWE-0",
                            "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N",
                            "impact": 0.0,
                            "why_missed": "Automated insight generation unavailable or unexpected format."
                        })
            except Exception as e:
                # await self.log(project_id, f"Insight batch {i // batch_size + 1} fallback: {str(e)}", "warning")
                pass
                for v in batch:
                    insights.append({
                        "id": v.get("id", "unknown_id"),
                        "cwe_id": "CWE-0",
                        "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N",
                        "impact": 0.0,
                        "why_missed": "Automated insight generation unavailable."
                    })

            # Delay between batches to avoid rate limiting
            if i + batch_size < len(vulns):
                await asyncio.sleep(2)

        state["insights"] = insights
        await self.save_output(project_id, {"insights": insights})
        await self.log(project_id, f"Insight generation complete: {len(insights)} insights", "success")
        await update_scan_progress(project_id, "analysis", self.name, 1.0, "Insight agent complete")
        return state
