"""Security Debate Agent — Agents challenge findings to verify exploitability."""

import json
from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from utils.llm_client import get_llm_response
from db.redis_client import update_scan_progress

SYSTEM_PROMPT = """You are a security debate moderator overseeing a verification process. Two expert perspectives must debate each vulnerability:

**Red Team (Attacker):** Argues the vulnerability IS exploitable and dangerous
**Blue Team (Defender):** Challenges the finding, argues it may be a false positive or mitigated

For each vulnerability, conduct this debate and reach a verdict:
- CONFIRMED: Vulnerability is real and exploitable
- LIKELY: Probably exploitable but needs more investigation
- DISPUTED: Significant doubt about exploitability
- FALSE_POSITIVE: Not a real vulnerability

Output valid JSON:
{
    "debates": [
        {
            "vulnerability_title": "...",
            "red_team_argument": "Why this IS exploitable...",
            "blue_team_argument": "Why this might NOT be exploitable...",
            "verdict": "CONFIRMED|LIKELY|DISPUTED|FALSE_POSITIVE",
            "confidence_adjustment": -20 to +20,
            "final_reasoning": "The consensus after debate..."
        }
    ],
    "overall_assessment": "..."
}"""


class SecurityDebateAgent(BaseAgent):
    name = "security_debate_agent"
    description = "Debates and verifies vulnerability findings through adversarial analysis"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        project_id = state["project_id"]
        vulns = state.get("vulnerabilities", [])
        exploits = state.get("exploits", [])

        if not vulns:
            await self.log(project_id, "No vulnerabilities to debate")
            state["debate_results"] = []
            return state

        await self.log(project_id, f"Starting security debate on {len(vulns)} findings")
        await update_scan_progress(project_id, "analysis", self.name, 0.1, "Debating vulnerability findings...")

        exploit_map = {}
        for e in exploits:
            exploit_map[e.get("vulnerability_title", "")] = e

        user_prompt = f"""Conduct an adversarial security debate on these findings:

VULNERABILITIES:
{json.dumps(vulns[:15], indent=2, default=str)}

EXPLOIT DETAILS:
{json.dumps(exploits[:10], indent=2, default=str)}

For each vulnerability, have Red Team and Blue Team debate its validity.
Be rigorous — real security teams challenge their own findings."""

        try:
            response = await get_llm_response(SYSTEM_PROMPT, user_prompt, json_mode=True, max_tokens=4096)
            debate_results = json.loads(response)
        except Exception as e:
            await self.log(project_id, f"Debate agent error: {str(e)}", "warning")
            debate_results = {"debates": [], "overall_assessment": "Debate skipped due to error"}

        # Adjust confidence based on debate results
        debate_map = {d.get("vulnerability_title", ""): d for d in debate_results.get("debates", [])}
        for v in vulns:
            debate = debate_map.get(v.get("title", ""), {})
            if debate:
                adj = debate.get("confidence_adjustment", 0)
                v["confidence"] = max(0, min(100, v.get("confidence", 50) + adj))
                v["debate_verdict"] = debate.get("verdict", "LIKELY")

        # Remove false positives
        vulns = [v for v in vulns if v.get("debate_verdict", "LIKELY") != "FALSE_POSITIVE"]

        await self.save_output(project_id, debate_results)
        confirmed = sum(1 for d in debate_results.get("debates", []) if d.get("verdict") == "CONFIRMED")
        await self.log(
            project_id,
            f"Debate complete: {confirmed} confirmed, {len(vulns)} remain after filtering",
            "success",
        )
        await update_scan_progress(project_id, "analysis", self.name, 1.0, "Security debate complete")

        state["vulnerabilities"] = vulns
        state["debate_results"] = debate_results.get("debates", [])
        return state
