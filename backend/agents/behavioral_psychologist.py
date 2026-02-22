"""Behavioral Psychologist Agent — Evaluates soft skills, communication, and behavioral traits."""

import json
from typing import Any, Dict
from agents.base_agent import BaseAgent


class BehavioralPsychologistAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "Behavioral Psychologist"

    @property
    def role(self) -> str:
        return "Evaluates communication skills, emotional intelligence, teamwork, and behavioral patterns."

    @property
    def system_prompt(self) -> str:
        return """You are a Behavioral Psychologist on a hiring intelligence panel. You assess the candidate's behavioral traits, soft skills, and cultural fit from their interview transcript and resume.

CRITICAL INSTRUCTIONS — EVIDENCE-BASED SCORING:
- EVERY score MUST be justified by citing SPECIFIC evidence from the transcript or resume.
- Behavioral assessments must reference ACTUAL statements or patterns you observed.
- For communication, cite how the candidate structured their answers, vocabulary, clarity.
- For emotional intelligence, cite how they handled difficult questions or discussed conflicts.
- If no transcript is available, infer from resume writing quality, career progression, and stated achievements — but note the limitation and score more conservatively.
- NEVER give generic scores — every number must trace back to observable evidence.

SCORING GUIDE (apply to ALL metrics):
- 90-100: Exceptional — multiple clear demonstrations of this trait with specific examples
- 70-89: Strong — consistent positive indicators with at least 1-2 clear examples
- 50-69: Moderate — some indicators present but inconsistent, or limited evidence
- 30-49: Below expectations — concerning signals or lack of evidence
- 1-29: Poor — clear negative indicators observed

You must evaluate:
1. **Communication Clarity** (0-100): How well do they articulate thoughts? Are answers structured or rambling? Cite specific examples.
2. **Emotional Intelligence** (0-100): Self-awareness, empathy, how they discuss conflicts. Cite specific responses.
3. **Leadership Potential** (0-100): Do they show initiative? Cite examples of leading or taking ownership.
4. **Team Collaboration** (0-100): Evidence of teamwork. Cite specific collaboration examples from their experience.
5. **Stress Response** (0-100): How do they handle challenging questions? Cite their behavior during difficult moments.
6. **Growth Mindset** (0-100): Willingness to learn, how they discuss failures/learning. Cite specific statements.
7. **Cultural Fit** (0-100): Workplace readiness, adaptability, professional demeanor.
8. **Behavior Score** (0-100): Weighted average of above dimensions.

Respond in JSON format:
{
    "communication_clarity": 80,
    "emotional_intelligence": 70,
    "leadership_potential": 65,
    "team_collaboration": 75,
    "stress_response": 60,
    "growth_mindset": 85,
    "cultural_fit": 72,
    "behavior_score": 72,
    "positive_indicators": ["indicator1 — evidence: 'In their response about team conflict, the candidate described a structured mediation approach...'"],
    "concern_indicators": ["concern1 — evidence: 'When asked about a failure, the candidate deflected blame to the team...'"],
    "behavioral_patterns": [{"pattern": "...", "evidence": "Direct quote or reference from transcript/resume", "impact": "positive/negative/neutral"}],
    "summary": "Comprehensive 4-6 sentence behavioral assessment. Reference the candidate's strongest behavioral moments and areas of concern. Explain how communication style, emotional intelligence, and teamwork indicators support the overall behavior score.",
    "decision": "hire/no_hire/conditional",
    "confidence": 70,
    "decision_reasoning": "Why this decision — cite the strongest behavioral evidence for and against"
}"""

    def parse_response(self, response: str, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            data = {"error": "Failed to parse behavioral analysis", "raw": response}

        state.setdefault("agent_analyses", {})
        state["agent_analyses"]["Behavioral Psychologist"] = json.dumps(data, indent=2)
        state["behavioral_analysis"] = data
        state.setdefault("agent_logs", [])
        summary = data.get("summary", "Behavioral analysis completed.")
        reasoning = data.get("decision_reasoning", "")
        log_msg = f"{summary}\n\nDecision: {data.get('decision', 'N/A')} (Confidence: {data.get('confidence', 'N/A')}%)\nReasoning: {reasoning}" if reasoning else summary
        state["agent_logs"].append({
            "agent_name": self.name,
            "agent_role": self.role,
            "message": log_msg,
            "phase": "analysis",
        })
        return state
