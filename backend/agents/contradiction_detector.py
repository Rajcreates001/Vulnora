"""Contradiction Detection Agent — Identifies discrepancies between resume and transcript."""

import json
from typing import Any, Dict
from agents.base_agent import BaseAgent


class ContradictionDetectorAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "Contradiction Detector"

    @property
    def role(self) -> str:
        return "Identifies contradictions and discrepancies between resume claims and interview responses."

    @property
    def system_prompt(self) -> str:
        return """You are a Contradiction Detection Specialist on a hiring intelligence panel. Your critical job is to find discrepancies between what the candidate claims on their resume and what they demonstrate in their interview.

CRITICAL INSTRUCTIONS — EVIDENCE-BASED ANALYSIS:
- You MUST quote or reference SPECIFIC text from both the resume AND transcript for every contradiction.
- Format: "Resume says: '...' but in the interview: '...'"
- If no interview transcript is available, compare resume claims against internal consistency and industry standards.
- Do NOT fabricate contradictions — only flag what you can PROVE with textual evidence.
- A contradiction means ACTUAL conflicting information, not just missing detail.

You must identify:
1. **Skill Contradictions**: Skills claimed on resume but not demonstrated in interview
   Example: Claims "Expert in Kubernetes" but cannot explain pods vs containers
2. **Experience Contradictions**: Experience claimed but answers suggest otherwise
   Example: Claims "5 years React" but confused about hooks
3. **Achievement Contradictions**: Achievements that don't align with demonstrated knowledge
4. **Timeline Inconsistencies**: Dates or durations that don't add up
5. **Depth Mismatches**: Claims of expertise with only surface-level knowledge

For each contradiction, you MUST provide:
- EXACT text from resume (the claim)
- EXACT text from interview or specific evidence (the contradiction)
- Severity: low / medium / high / critical
- Detailed explanation of WHY this is a contradiction

SCORING GUIDE for consistency_score:
- 90-100: Highly consistent — all claims verified, no contradictions
- 70-89: Mostly consistent — minor discrepancies only
- 50-69: Moderate concerns — some notable contradictions
- 30-49: Significant inconsistencies — multiple material contradictions
- 1-29: Major red flags — pervasive contradictions undermining credibility

Respond in JSON format:
{
    "contradictions": [
        {
            "claim": "Resume states: 'Led migration to Kubernetes-based microservices architecture'",
            "evidence": "In interview Q3, candidate said 'I haven't directly worked with container orchestration' — directly contradicting the resume claim",
            "severity": "critical",
            "explanation": "Leading a Kubernetes migration requires deep container orchestration knowledge. The candidate's inability to discuss basic Kubernetes concepts suggests the resume claim is significantly exaggerated."
        }
    ],
    "consistency_score": 45,
    "total_claims_checked": 12,
    "verified_claims": 7,
    "contradicted_claims": 3,
    "unverifiable_claims": 2,
    "overall_credibility": "low/medium/high",
    "summary": "Comprehensive 3-5 sentence credibility assessment with specific evidence references",
    "red_flags": ["flag1 — with specific evidence"],
    "decision": "hire/no_hire/conditional",
    "confidence": 70,
    "decision_reasoning": "Specific explanation of how credibility findings affect hiring recommendation"
}"""

    def build_prompt(self, state: Dict[str, Any]) -> str:
        resume = state.get("resume_text", "")
        transcript = state.get("transcript_text", "")
        job_desc = state.get("job_description", "")
        resume_analysis = state.get("resume_analysis", {})

        claims = resume_analysis.get("claims", [])
        claims_text = "\n".join([f"- {c.get('claim', c) if isinstance(c, dict) else c}" for c in claims])

        return f"""
## Job Description
{job_desc}

## Candidate Resume
{resume}

## Interview Transcript
{transcript}

## Extracted Resume Claims
{claims_text if claims_text else "No specific claims extracted yet."}

Carefully compare the resume claims against interview responses. Find ALL contradictions, inconsistencies, and credibility issues. Be thorough and specific with evidence.

## Previous Agent Analyses
{self._format_previous_analyses(state)}
"""

    def parse_response(self, response: str, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            data = {"error": "Failed to parse contradiction analysis", "raw": response}

        state.setdefault("agent_analyses", {})
        state["agent_analyses"]["Contradiction Detector"] = json.dumps(data, indent=2)
        state["contradiction_analysis"] = data
        state.setdefault("agent_logs", [])
        summary = data.get("summary", "Contradiction detection completed.")
        reasoning = data.get("decision_reasoning", "")
        contradictions_count = len(data.get("contradictions", []))
        log_msg = f"{summary}\n\nFound {contradictions_count} contradictions. Credibility: {data.get('overall_credibility', 'N/A')}. Consistency score: {data.get('consistency_score', 'N/A')}/100.\nDecision: {data.get('decision', 'N/A')} (Confidence: {data.get('confidence', 'N/A')}%)" if reasoning or contradictions_count else summary
        state["agent_logs"].append({
            "agent_name": self.name,
            "agent_role": self.role,
            "message": log_msg,
            "phase": "analysis",
        })
        return state
