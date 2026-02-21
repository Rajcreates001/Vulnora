"""Alert Reduction Agent — Deduplicates, groups, and prioritizes vulnerabilities to reduce alert fatigue."""

from agents.base_agent import BaseAgent
from db.redis_client import update_scan_progress
from typing import Any, Dict, List
import hashlib

class AlertReductionAgent(BaseAgent):
    name = "alert_reduction_agent"
    description = "Deduplicates, groups, and prioritizes vulnerabilities to reduce alert fatigue."

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        project_id = state["project_id"]
        vulns = state.get("vulnerabilities", [])
        await self.log(project_id, "Reducing alert fatigue: deduplication, grouping, prioritization")
        await update_scan_progress(project_id, "analysis", self.name, 0.1, "Reducing alert fatigue...")

        # Deduplicate by hash of title+location+type
        seen = set()
        deduped = []
        for v in vulns:
            key = hashlib.sha256(f"{v.get('title','')}-{v.get('location','')}-{v.get('type','')}".encode()).hexdigest()
            if key not in seen:
                seen.add(key)
                deduped.append(v)

        # Group by type
        grouped = {}
        for v in deduped:
            t = v.get("type", "Other")
            grouped.setdefault(t, []).append(v)

        # Prioritize: critical > high > medium > low > info
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        prioritized = []
        for t, vulns in grouped.items():
            vulns.sort(key=lambda v: severity_order.get(v.get("severity", "medium").lower(), 2))
            prioritized.extend(vulns)

        state["vulnerabilities"] = prioritized
        state["alert_reduction"] = {
            "deduplicated_count": len(deduped),
            "grouped_types": list(grouped.keys()),
            "prioritized_count": len(prioritized)
        }
        await self.save_output(project_id, state["alert_reduction"])
        await self.log(project_id, f"Alert reduction complete: {len(prioritized)} prioritized", "success")
        await update_scan_progress(project_id, "analysis", self.name, 1.0, "Alert reduction complete")
        return state
