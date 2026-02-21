"""Report Generation Agent — Creates professional vulnerability reports."""

import json
from typing import Any, Dict, List
from datetime import datetime, timezone

from agents.base_agent import BaseAgent
from utils.llm_client import get_llm_response
from db.redis_client import update_scan_progress

SYSTEM_PROMPT = """You are a senior security consultant writing a professional vulnerability assessment report. The report should be:

1. **Executive Summary**: High-level overview for management (2-3 paragraphs)
2. **Key Findings**: Critical vulnerabilities that need immediate attention
3. **Recommendations**: Prioritized remediation steps
4. **Overall Risk Rating**: Based on aggregate findings

Write in a professional, clear, and actionable tone. Avoid jargon where possible.
Make it suitable for both technical and non-technical stakeholders.

Output valid JSON:
{
    "executive_summary": "...",
    "key_findings": ["..."],
    "recommendations": ["..."],
    "overall_risk_rating": "Critical|High|Medium|Low",
    "overall_risk_score": 0-100,
    "remediation_priority": [
        {"title": "...", "priority": "Immediate|Short-term|Long-term", "description": "..."}
    ],
    "conclusion": "..."
}"""


class ReportGenerationAgent(BaseAgent):
    name = "report_generation_agent"
    description = "Generates professional security assessment reports"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        project_id = state["project_id"]
        vulns = state.get("vulnerabilities", [])
        exploits = state.get("exploits", [])
        patches = state.get("patches", [])
        debate_results = state.get("debate_results", [])
        recon = state.get("recon_results", {})

        await self.log(project_id, "Generating security report")
        await update_scan_progress(project_id, "report", self.name, 0.1, "Generating professional report...")

        # Calculate summary stats
        severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for v in vulns:
            sev = v.get("severity", "Medium")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        user_prompt = f"""Generate a professional security assessment report:

PROJECT RECONNAISSANCE:
{json.dumps(recon.get('attack_surface_summary', ''), default=str)}
Technology Stack: {json.dumps(recon.get('technology_stack', []), default=str)}

VULNERABILITY SUMMARY:
Total: {len(vulns)}
Critical: {severity_counts['Critical']}
High: {severity_counts['High']}
Medium: {severity_counts['Medium']}
Low: {severity_counts['Low']}

TOP VULNERABILITIES:
{json.dumps(vulns[:10], indent=2, default=str)}

EXPLOIT CAPABILITIES:
{json.dumps([{"title": e.get("vulnerability_title"), "complexity": e.get("attack_complexity")} for e in exploits[:10]], indent=2, default=str)}

DEBATE RESULTS:
{json.dumps(debate_results[:10], indent=2, default=str)}

PATCHES AVAILABLE: {len(patches)} patches generated

Create a comprehensive, professional security report."""

        try:
            response = await get_llm_response(SYSTEM_PROMPT, user_prompt, json_mode=True, max_tokens=4096)
            report_content = json.loads(response)
        except Exception as e:
            # await self.log(project_id, f"Report generation fallback: {str(e)}", "warning")
            report_content = self._generate_basic_report(vulns, severity_counts)

        # Build complete report
        report = {
            "project_id": project_id,
            "executive_summary": report_content.get("executive_summary", ""),
            "total_vulnerabilities": len(vulns),
            "critical_count": severity_counts["Critical"],
            "high_count": severity_counts["High"],
            "medium_count": severity_counts["Medium"],
            "low_count": severity_counts["Low"],
            "overall_risk_score": report_content.get("overall_risk_score", 0),
            "overall_risk_rating": report_content.get("overall_risk_rating", "Medium"),
            "key_findings": report_content.get("key_findings", []),
            "recommendations": report_content.get("recommendations", []),
            "remediation_priority": report_content.get("remediation_priority", []),
            "conclusion": report_content.get("conclusion", ""),
            "attack_paths": self._build_attack_paths(exploits),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        await self.save_output(project_id, report)
        await self.log(project_id, f"Report generated. Overall risk: {report['overall_risk_rating']}", "success")
        await update_scan_progress(project_id, "report", self.name, 1.0, "Report generation complete")

        state["report"] = report
        return state

    def _build_attack_paths(self, exploits: List[Dict]) -> List[Dict]:
        """Build attack path graphs from exploit data."""
        paths = []
        for exploit in exploits:
            attack_path = exploit.get("attack_path", [])
            if attack_path:
                nodes = []
                edges = []
                for i, step in enumerate(attack_path):
                    node_id = f"node_{i}"
                    nodes.append({
                        "id": node_id,
                        "label": step.get("node", f"Step {i+1}"),
                        "node_type": step.get("type", "function"),
                        "data": {"description": step.get("description", "")},
                    })
                    if i > 0:
                        edges.append({
                            "id": f"edge_{i-1}_{i}",
                            "source": f"node_{i-1}",
                            "target": node_id,
                            "label": "",
                        })
                paths.append({
                    "vulnerability": exploit.get("vulnerability_title", ""),
                    "nodes": nodes,
                    "edges": edges,
                })
        return paths

    def _generate_basic_report(self, vulns: List[Dict], counts: Dict) -> Dict:
        total = len(vulns)
        if not vulns:
            return {
                "executive_summary": "No vulnerabilities found.",
                "key_findings": [],
                "recommendations": [],
                "overall_risk_rating": "Low",
                "overall_risk_score": 0,
                "remediation_priority": [],
                "conclusion": "No security issues detected.",
            }

        avg_score = sum(v.get("risk_score", 50) for v in vulns) / total
        score = round(avg_score, 1)

        if score >= 90: rating = "Critical"
        elif score >= 70: rating = "High"
        elif score >= 40: rating = "Medium"
        else: rating = "Low"

        return {
            "executive_summary": f"Security assessment identified {total} vulnerabilities: "
                f"{counts['Critical']} critical, {counts['High']} high, "
                f"{counts['Medium']} medium, and {counts['Low']} low severity issues. "
                f"Immediate remediation is recommended for all critical and high-severity findings.",
            "key_findings": [v.get("title", "") for v in vulns[:5]],
            "recommendations": [
                "Address all critical vulnerabilities immediately",
                "Implement input validation across all user-facing endpoints",
                "Review authentication and authorization mechanisms",
                "Remove all hardcoded secrets and use environment variables",
                "Enable security headers and CORS policies",
            ],
            "overall_risk_rating": rating,
            "overall_risk_score": score,
            "remediation_priority": [],
            "conclusion": f"The application requires security improvements. {counts['Critical'] + counts['High']} high-priority issues need immediate attention.",
        }
