"""Risk Prioritization Agent — Assigns severity scores and calculates CVSS-like ratings."""

import json
from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from utils.llm_client import get_llm_response
from db.redis_client import update_scan_progress

SYSTEM_PROMPT = """You are a security risk analyst. Given vulnerabilities with their exploit details and patches, calculate precise risk scores.

For each vulnerability, assess:
1. **Severity**: Critical (90-100), High (70-89), Medium (40-69), Low (0-39)
2. **Risk Score** (0-100): Overall risk considering all factors
3. **Confidence** (0-100): How confident we are this is a real vulnerability
4. **Exploitability** (0-100): How easy it is to exploit
5. **Impact** (0-100): Business impact if exploited

Consider:
- Attack complexity (network vs local, authentication required)
- Scope (does it affect other components)
- Data sensitivity
- Availability impact
- Whether a patch exists

Output valid JSON:
{
    "scored_vulnerabilities": [
        {
            "title": "...",
            "severity": "Critical|High|Medium|Low",
            "risk_score": 0-100,
            "confidence": 0-100,
            "exploitability": 0-100,
            "impact": 0-100,
            "cvss_vector": "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
            "justification": "..."
        }
    ],
    "overall_risk_score": 0-100,
    "risk_summary": "..."
}"""


class RiskPrioritizationAgent(BaseAgent):
    name = "risk_prioritization_agent"
    description = "Assigns severity scores and calculates CVSS-like risk ratings"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        project_id = state["project_id"]
        vulns = state.get("vulnerabilities", [])
        exploits = state.get("exploits", [])
        patches = state.get("patches", [])

        if not vulns:
            await self.log(project_id, "No vulnerabilities to score")
            state["risk_scores"] = []
            return state

        await self.log(project_id, f"Scoring {len(vulns)} vulnerabilities")
        await update_scan_progress(project_id, "analysis", self.name, 0.2, "Calculating risk scores...")

        user_prompt = f"""Score these vulnerabilities with precise risk ratings:

VULNERABILITIES:
{json.dumps(vulns, indent=2, default=str)}

EXPLOIT DETAILS:
{json.dumps(exploits[:10], indent=2, default=str)}

PATCHES AVAILABLE:
{json.dumps([{"title": p.get("vulnerability_title"), "has_patch": bool(p.get("patched_code"))} for p in patches], indent=2, default=str)}

Provide accurate CVSS-like scoring for each vulnerability."""

        try:
            response = await get_llm_response(SYSTEM_PROMPT, user_prompt, json_mode=True)
            risk_results = json.loads(response)
        except Exception as e:
            # await self.log(project_id, f"Risk scoring fallback: {str(e)}", "warning")
            risk_results = self._fallback_scoring(vulns)

        # Merge scores back into vulnerabilities
        scored = risk_results.get("scored_vulnerabilities", [])
        score_map = {s.get("title", ""): s for s in scored}

        for v in vulns:
            score_data = score_map.get(v.get("title", ""), {})
            v["severity"] = score_data.get("severity", v.get("severity", "Medium"))
            v["risk_score"] = score_data.get("risk_score", v.get("risk_score", 50))
            v["confidence"] = score_data.get("confidence", v.get("confidence", 50))
            v["exploitability"] = score_data.get("exploitability", v.get("exploitability", 50))
            v["impact"] = score_data.get("impact", v.get("impact", 50))
            v["cvss_vector"] = score_data.get("cvss_vector", "")

        await self.save_output(project_id, risk_results)
        overall = risk_results.get("overall_risk_score", 0)
        await self.log(project_id, f"Risk scoring complete. Overall risk: {overall}/100", "success")
        await update_scan_progress(project_id, "analysis", self.name, 1.0, "Risk scoring complete")

        state["vulnerabilities"] = vulns
        state["risk_scores"] = scored
        return state

    def _fallback_scoring(self, vulns: List[Dict]) -> Dict:
        severity_scores = {"Critical": 90, "High": 75, "Medium": 50, "Low": 25}
        scored = []
        for v in vulns:
            sev = v.get("severity", "Medium")
            base = severity_scores.get(sev, 50)
            scored.append({
                "title": v.get("title", ""),
                "severity": sev,
                "risk_score": base,
                "confidence": v.get("confidence", 60),
                "exploitability": base - 10,
                "impact": base + 5,
                "cvss_vector": "",
                "justification": "Scored based on severity level",
            })
        overall = sum(s["risk_score"] for s in scored) / max(len(scored), 1)
        return {
            "scored_vulnerabilities": scored,
            "overall_risk_score": round(overall, 1),
            "risk_summary": f"Found {len(scored)} vulnerabilities with average risk score of {overall:.0f}/100",
        }
