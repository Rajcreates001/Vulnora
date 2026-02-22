"""Consensus Negotiator Agent — Synthesizes all agent opinions into a final decision."""

import json
from typing import Any, Dict
from agents.base_agent import BaseAgent


class ConsensusNegotiatorAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "Consensus Negotiator"

    @property
    def role(self) -> str:
        return "Synthesizes all agent opinions, mediates disagreements, and produces the final hiring decision."

    @property
    def system_prompt(self) -> str:
        return """You are the Consensus Negotiator on a hiring intelligence panel. You synthesize all agent analyses into a final, well-reasoned hiring decision.

Your responsibilities:
1. Review ALL agent analyses thoroughly
2. Identify areas of agreement and disagreement between agents
3. Weigh opinions using this formula:
   - Technical Depth = 40%
   - Behavioral Assessment = 20%
   - Risk Assessment = 20%
   - Business Fit = 20%
4. Produce the FINAL hiring decision with RIGOROUS evidence-based reasoning

DECISION CATEGORIES (you MUST use exactly one of these):
- "Strong Hire" — Exceptional candidate, clearly exceeds requirements
- "Hire" — Good candidate, meets requirements with minor gaps
- "Hold" — Uncertain, has potential but significant concerns exist
- "Reject" — Does not meet requirements or has critical disqualifying issues

═══════════════════════════════════════════════════════════
CRITICAL: THE "reasoning" FIELD IS THE MOST IMPORTANT OUTPUT.
═══════════════════════════════════════════════════════════

The reasoning field will be READ AND EVALUATED by an interviewer to determine if the AI panel made the right call. Your reasoning MUST be:

1. **STRUCTURED** — Use this exact format in the reasoning:
   CANDIDATE PROFILE: [1-2 sentences about who the candidate is based on resume]
   
   TECHNICAL ASSESSMENT: [What the Technical Depth Analyst found, their score, and WHY — cite specific evidence from resume/transcript]
   
   BEHAVIORAL ASSESSMENT: [What the Behavioral Psychologist found — cite specific communication patterns and behavioral evidence]
   
   DOMAIN FIT: [What the Domain Expert found — how many JD requirements are covered and which critical ones are missing]
   
   CREDIBILITY CHECK: [What the Contradiction Detector found — any red flags with specific examples]
   
   BUSINESS FIT: [What the Hiring Manager concluded — strategic value and concerns]
   
   SCORE JUSTIFICATION: [Explain the weighted calculation: "Technical (X × 0.4) + Behavioral (Y × 0.2) + Risk (Z × 0.2) + Business (W × 0.2) = Final"]
   
   KEY STRENGTHS: [Top 2-3 strengths with EVIDENCE]
   
   KEY CONCERNS: [Top 2-3 concerns with EVIDENCE]
   
   FINAL VERDICT: [Decision + WHY — the DEFINITIVE reason this candidate should/shouldn't be hired]

2. **EVIDENCE-BASED** — Every claim must reference specific text from resume, transcript, or agent analyses
3. **SPECIFIC** — No generic statements like "the candidate is a good fit" — instead: "the candidate's 4 years of Python backend experience (resume) plus demonstrated knowledge of async patterns (interview Q3) align with the Senior Backend Developer JD requirement"
4. **HONEST** — If evidence is insufficient, say so. If agents disagree, explain why one view is prioritized.

SCORING RULES:
- ALL scores MUST be non-zero (minimum 1).
- Scores should be a WEIGHTED SYNTHESIS of individual agent scores, not new guesses.
- Show reasoning for each score: "technical_score is 72 because the Technical Depth Analyst scored 75 on depth and 68 on architecture, weighted toward depth since the JD emphasizes backend skills"
- technical_score: Rate coding ability, system design, algorithms (1-100)
- behavior_score: Rate teamwork, communication style, attitude (1-100)
- domain_score: Rate domain knowledge relevant to the job (1-100)
- communication_score: Rate clarity, articulation, explanation ability (1-100)
- learning_potential: Rate adaptability, growth mindset, curiosity (1-100)
- risk_score: Rate overall hiring risk (1-100, lower is better)
- confidence: Your confidence in the decision (1-100)

Respond in JSON format:
{
    "final_decision": "Strong Hire/Hire/Hold/Reject",
    "confidence": 78,
    "technical_score": 72,
    "behavior_score": 75,
    "risk_score": 35,
    "learning_potential": 80,
    "domain_score": 68,
    "communication_score": 77,
    "reasoning": "CANDIDATE PROFILE: [Name] is a [X years] experienced [role] who has worked at [companies]. Their resume highlights [key skills] relevant to the [job title] role.\\n\\nTECHNICAL ASSESSMENT: The Technical Depth Analyst scored the candidate at [X] for technical depth. Specifically, [cite evidence — e.g., 'the candidate correctly explained microservices patterns and demonstrated hands-on Docker experience (Q2), but struggled with system design scalability questions (Q5), only suggesting vertical scaling']. This suggests [conclusion].\\n\\nBEHAVIORAL ASSESSMENT: The Behavioral Psychologist scored communication at [X] and emotional intelligence at [Y]. Evidence: [cite — e.g., 'the candidate used the STAR method effectively when discussing team conflicts (Q4), showing structured thinking. However, they deflected responsibility when discussing a failed project (Q6)'].\\n\\nDOMAIN FIT: The Domain Expert found the candidate covers [X of Y] JD requirements. Strengths: [cite]. Critical gaps: [cite].\\n\\nCREDIBILITY CHECK: The Contradiction Detector found [X] contradictions with [severity]. Most notable: [cite specific contradiction].\\n\\nBUSINESS FIT: The Hiring Manager assessed business fit at [X], noting [cite strategic value and concerns].\\n\\nSCORE JUSTIFICATION: Technical (72 × 0.4 = 28.8) + Behavioral (75 × 0.2 = 15.0) + Risk-adjusted (65 × 0.2 = 13.0) + Business (68 × 0.2 = 13.6) = Weighted 70.4.\\n\\nKEY STRENGTHS: 1) [strength with evidence] 2) [strength with evidence]\\n\\nKEY CONCERNS: 1) [concern with evidence] 2) [concern with evidence]\\n\\nFINAL VERDICT: [Decision] — [compelling 2-3 sentence explanation of WHY this is the right call, referencing the most important evidence]",
    "agent_debate": [
        {
            "agent_name": "Resume Analyst",
            "message": "Evidence-based argument citing specific findings...",
            "stance": "hire",
            "responding_to": null
        },
        {
            "agent_name": "Contradiction Detector",
            "message": "Counter-argument citing specific contradictions found...",
            "stance": "conditional",
            "responding_to": "Resume Analyst"
        },
        {
            "agent_name": "Technical Depth Analyst",
            "message": "Technical perspective with specific score justification...",
            "stance": "hire",
            "responding_to": "Contradiction Detector"
        },
        {
            "agent_name": "Behavioral Psychologist",
            "message": "Behavioral perspective with evidence...",
            "stance": "hire",
            "responding_to": null
        },
        {
            "agent_name": "Domain Expert",
            "message": "Domain fit assessment with JD comparison...",
            "stance": "conditional",
            "responding_to": null
        },
        {
            "agent_name": "Hiring Manager",
            "message": "Final business perspective synthesizing all views...",
            "stance": "hire",
            "responding_to": "Domain Expert"
        }
    ],
    "skill_gaps": [
        {
            "skill": "Kubernetes",
            "current_level": "beginner",
            "required_level": "intermediate",
            "gap_severity": "high",
            "training_estimate": "3-4 weeks"
        }
    ],
    "contradictions": [
        {
            "claim": "Resume states: '5 years Kubernetes experience'",
            "evidence": "In interview Q5, candidate said: 'I have basic familiarity with containers' — contradicting the expert-level claim",
            "severity": "critical",
            "explanation": "Fundamental knowledge gap between claimed and demonstrated expertise"
        }
    ],
    "risk_analysis": {
        "hiring_risk_score": 45,
        "learning_potential_score": 80,
        "attrition_risk": 25,
        "confidence_percentage": 78,
        "risk_factors": ["factor1 — with specific evidence"],
        "mitigating_factors": ["factor1 — with specific evidence"]
    },
    "why_not_hire": {
        "major_weaknesses": ["weakness1 — with evidence"],
        "evidence": ["specific evidence from interview/resume"],
        "risk_justification": "Detailed risk justification citing specific concerns",
        "improvement_suggestions": ["suggestion1"],
        "thirty_day_plan": [
            "Week 1: Focus on...",
            "Week 2: Practice...",
            "Week 3: Build...",
            "Week 4: Review..."
        ]
    },
    "improvement_roadmap": {
        "week_1": ["task1"],
        "week_2": ["task1"],
        "week_3": ["task1"],
        "week_4": ["task1"],
        "resources": ["resource1"]
    },
    "agent_opinions": [
        {
            "agent_name": "Resume Analyst",
            "role": "Resume Analysis",
            "decision": "hire",
            "confidence": 75,
            "reasoning": "Evidence-based reasoning from this agent's analysis...",
            "key_concerns": [],
            "key_strengths": ["strength1 with evidence"]
        }
    ]
}"""

    def build_prompt(self, state: Dict[str, Any]) -> str:
        analyses = state.get("agent_analyses", {})
        analyses_text = "\n\n".join([f"### {name}\n{analysis}" for name, analysis in analyses.items()])

        resume = state.get("resume_text", "")
        transcript = state.get("transcript_text", "")

        resume_section = f"## Candidate Resume (FULL TEXT — reference this for evidence)\n{resume}" if resume else ""
        transcript_section = f"## Interview Transcript (FULL TEXT — reference this for evidence)\n{transcript}" if transcript else "## Interview Transcript\n(No interview transcript available — evaluate based on resume and job description only. Note this limitation in your reasoning.)"

        return f"""
## Job Description
{state.get('job_description', '')}

{resume_section}

{transcript_section}

## All Agent Analyses (read EVERY analysis carefully)
{analyses_text}

═══════════════════════════════════════════════════════════
YOU ARE THE FINAL DECISION MAKER.
═══════════════════════════════════════════════════════════

Instructions:
1. Read EVERY agent analysis above carefully
2. Extract the individual scores each agent gave
3. Your final scores should be a WEIGHTED SYNTHESIS of agent scores — NOT random numbers
4. Your reasoning MUST follow the structured format from your system prompt
5. The reasoning field will be evaluated by a human interviewer — it MUST be thorough and convincing

DECISION MUST be exactly one of: "Strong Hire", "Hire", "Hold", or "Reject".

For the agent_debate, simulate a REAL debate where agents argue based on their ACTUAL findings (reference specific scores and evidence from their analyses above).

Apply weighted scoring:
- Technical Depth = 40%
- Behavioral Assessment = 20%
- Risk Assessment = 20%
- Business Fit = 20%

CRITICAL REMINDERS:
- Every score must be non-zero and derived from agent analyses (not invented)
- The 'reasoning' field MUST be at least 300 words with the structured format
- Every claim in reasoning MUST cite evidence from resume, transcript, or agent analyses
- If you can't find evidence for something, say so honestly
- The human interviewer will check if your reasoning matches the evidence — be accurate
"""

    def parse_response(self, response: str, state: Dict[str, Any]) -> Dict[str, Any]:
        import logging
        logger = logging.getLogger(__name__)

        data = {}
        try:
            data = json.loads(response)
            logger.info(f"[Consensus] Parsed JSON successfully. Keys: {list(data.keys())}")
            logger.info(f"[Consensus] final_decision={data.get('final_decision')}, "
                        f"confidence={data.get('confidence')}, "
                        f"tech_score={data.get('technical_score')}")
        except json.JSONDecodeError as e:
            logger.error(f"[Consensus] JSON parse failed: {e}")
            logger.error(f"[Consensus] Raw response (first 500): {response[:500]}")
            # Try to extract partial JSON
            try:
                # Sometimes the LLM returns truncated JSON - try to fix it
                cleaned = response.strip()
                if cleaned.startswith("{") and not cleaned.endswith("}"):
                    # Truncated JSON, try to close it
                    cleaned += '}'
                data = json.loads(cleaned)
                logger.info("[Consensus] Recovered from truncated JSON")
            except json.JSONDecodeError:
                data = {"error": "Failed to parse consensus JSON", "raw_preview": response[:300]}

        # Validate critical fields exist and are non-empty
        if data.get("error") or not data.get("final_decision"):
            logger.warning(f"[Consensus] Response is incomplete or error: {data.get('error', 'no final_decision')}")

        state["consensus"] = data
        state.setdefault("agent_logs", [])
        state["agent_logs"].append({
            "agent_name": self.name,
            "agent_role": self.role,
            "message": data.get("reasoning", "Consensus decision reached."),
            "phase": "consensus",
        })
        return state
