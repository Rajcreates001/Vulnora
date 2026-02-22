"""Bias Auditor Agent — Ensures fair evaluations free from bias."""

import json
from typing import Any, Dict
from agents.base_agent import BaseAgent


class BiasAuditorAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "Bias Auditor"

    @property
    def role(self) -> str:
        return "Audits the evaluation process for potential biases and ensures fairness."

    @property
    def system_prompt(self) -> str:
        return """You are a Bias Auditor on a hiring intelligence panel. Your critical role is to ensure the evaluation process is fair and free from cognitive biases.

Review all previous agent analyses and check for:
1. **Confirmation Bias**: Are agents only looking for evidence that supports their initial impression?
2. **Halo/Horn Effect**: Is one strong/weak area unduly influencing the overall assessment?
3. **Affinity Bias**: Are agents favoring candidates similar to themselves?
4. **Anchoring Bias**: Are early assessments unduly influencing later ones?
5. **Gender/Age/Cultural Bias**: Any language suggesting demographic bias?
6. **Strictness/Leniency Bias**: Are standards being applied consistently?

Respond in JSON format:
{
    "biases_detected": [
        {
            "bias_type": "confirmation_bias",
            "agent": "Technical Depth Analyst",
            "description": "Agent focused only on weaknesses after finding one gap",
            "severity": "medium",
            "recommendation": "Re-evaluate considering positive technical indicators"
        }
    ],
    "fairness_score": 85,
    "adjustments_recommended": ["adjustment1"],
    "score_modifications": {
        "technical_score_adjustment": 0,
        "behavior_score_adjustment": 0,
        "risk_score_adjustment": 0
    },
    "summary": "Brief bias audit summary",
    "evaluation_is_fair": true
}"""

    def build_prompt(self, state: Dict[str, Any]) -> str:
        analyses = state.get("agent_analyses", {})
        analyses_text = "\n\n".join([f"### {name}\n{analysis}" for name, analysis in analyses.items()])

        return f"""
## All Agent Analyses to Audit
{analyses_text}

Review all agent analyses for potential biases. Be thorough in identifying any unfair evaluation patterns. Your goal is to ensure the candidate receives a fair and objective assessment.
"""

    def parse_response(self, response: str, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            data = {"error": "Failed to parse bias audit", "raw": response}

        state.setdefault("agent_analyses", {})
        state["agent_analyses"]["Bias Auditor"] = json.dumps(data, indent=2)
        state["bias_audit"] = data
        state.setdefault("agent_logs", [])
        state["agent_logs"].append({
            "agent_name": self.name,
            "agent_role": self.role,
            "message": data.get("summary", "Bias audit completed."),
            "phase": "audit",
        })
        return state
