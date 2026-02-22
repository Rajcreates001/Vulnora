"""Evaluation service — orchestrates the full hiring panel evaluation."""

import json
import logging
import uuid as uuid_mod
from datetime import datetime, timezone
from typing import Dict, Any, AsyncGenerator, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)

from models.db_models import Candidate, Evaluation, AgentLog
from graph.workflow import hiring_graph
from graph.workflow import (
    resume_agent,
    technical_agent,
    behavioral_agent,
    domain_agent,
    hiring_manager_agent,
    contradiction_agent,
    bias_agent,
    consensus_agent,
)
from services.cache import cache_service
from services.vector_store import get_vector_store

# Pipeline of agents to run in sequence for streaming evaluation
AGENT_PIPELINE = [
    {"name": "Resume Analyst", "description": "Analyzing resume and extracting claims...", "agent": resume_agent},
    {"name": "Technical Depth Analyst", "description": "Evaluating technical knowledge depth...", "agent": technical_agent},
    {"name": "Behavioral Psychologist", "description": "Assessing behavioral patterns and soft skills...", "agent": behavioral_agent},
    {"name": "Domain Expert", "description": "Validating domain-specific expertise...", "agent": domain_agent},
    {"name": "Contradiction Detector", "description": "Cross-referencing resume claims with interview responses...", "agent": contradiction_agent},
    {"name": "Hiring Manager", "description": "Evaluating business fit and team alignment...", "agent": hiring_manager_agent},
    {"name": "Bias Auditor", "description": "Auditing evaluation for potential biases...", "agent": bias_agent},
    {"name": "Consensus Negotiator", "description": "Synthesizing all opinions into final decision...", "agent": consensus_agent},
]


def _safe_score(value: Any, default: int = 30) -> int:
    """Safely convert a score to int, clamped 0-100. Default is 30 (conservative)."""
    if value is None:
        return default
    try:
        v = int(float(value))
        return max(0, min(100, v))
    except (ValueError, TypeError):
        return default


def _assess_transcript_quality(state: dict) -> str:
    """Assess overall transcript quality to inform scoring defaults."""
    transcript = state.get("transcript_text", "")
    if not transcript or len(transcript.strip()) < 50:
        return "no_transcript"

    lines = transcript.split("\n")
    candidate_lines = [l for l in lines if "Candidate" in l]
    if not candidate_lines:
        return "no_answers"

    short_count = 0
    for line in candidate_lines:
        parts = line.split(":", 2)
        answer = parts[-1].strip() if len(parts) > 1 else line.strip()
        words = answer.split()
        if len(words) <= 5:
            short_count += 1

    ratio = short_count / len(candidate_lines) if candidate_lines else 1
    if ratio > 0.7:
        return "very_poor"
    elif ratio > 0.4:
        return "poor"
    return "adequate"


def _build_initial_state(candidate, candidate_id: str) -> dict:
    """Build the initial state dict for the agent pipeline."""
    return {
        "resume_text": candidate.resume_text or "",
        "transcript_text": candidate.transcript_text or "",
        "job_description": candidate.job_description or "",
        "candidate_id": candidate_id,
        "agent_analyses": {},
        "agent_logs": [],
        "resume_analysis": {},
        "technical_analysis": {},
        "behavioral_analysis": {},
        "domain_analysis": {},
        "hiring_manager_analysis": {},
        "contradiction_analysis": {},
        "bias_audit": {},
        "consensus": {},
    }


def _build_agent_debate_from_analyses(state: dict) -> List[dict]:
    """Build a realistic agent debate from individual agent analyses when consensus fails."""
    debate = []
    technical = state.get("technical_analysis", {})
    behavioral = state.get("behavioral_analysis", {})
    domain = state.get("domain_analysis", {})
    hiring_mgr = state.get("hiring_manager_analysis", {})
    contradiction = state.get("contradiction_analysis", {})

    # Technical analyst opens
    tech_decision = technical.get("decision", "conditional")
    tech_summary = technical.get("summary", "Technical analysis completed.")
    tech_score = technical.get("technical_score", 0)
    if tech_summary and tech_score:
        debate.append({
            "agent_name": "Technical Depth Analyst",
            "message": f"Technical score: {tech_score}/100. {tech_summary}",
            "stance": tech_decision,
            "responding_to": None,
        })

    # Behavioral responds
    beh_decision = behavioral.get("decision", "conditional")
    beh_summary = behavioral.get("summary", "Behavioral analysis completed.")
    beh_score = behavioral.get("behavior_score", 0)
    if beh_summary and beh_score:
        debate.append({
            "agent_name": "Behavioral Psychologist",
            "message": f"Behavioral score: {beh_score}/100. {beh_summary}",
            "stance": beh_decision,
            "responding_to": "Technical Depth Analyst",
        })

    # Domain expert
    dom_decision = domain.get("decision", "conditional")
    dom_summary = domain.get("summary", "Domain assessment completed.")
    dom_score = domain.get("domain_score", 0)
    coverage = domain.get("jd_requirements_coverage", "")
    if dom_summary:
        msg = f"Domain score: {dom_score}/100. {coverage}. {dom_summary}" if coverage else f"Domain score: {dom_score}/100. {dom_summary}"
        debate.append({
            "agent_name": "Domain Expert",
            "message": msg,
            "stance": dom_decision,
            "responding_to": "Behavioral Psychologist",
        })

    # Contradiction detector
    con_decision = contradiction.get("decision", "conditional")
    con_summary = contradiction.get("summary", "")
    credibility = contradiction.get("overall_credibility", "unknown")
    contradictions_list = contradiction.get("contradictions", [])
    if con_summary or contradictions_list:
        msg = f"Overall credibility: {credibility}. Found {len(contradictions_list)} contradictions. {con_summary}"
        debate.append({
            "agent_name": "Contradiction Detector",
            "message": msg,
            "stance": con_decision,
            "responding_to": "Domain Expert",
        })

    # Hiring manager synthesizes
    hm_decision = hiring_mgr.get("decision", "conditional")
    hm_summary = hiring_mgr.get("summary", "")
    if hm_summary:
        debate.append({
            "agent_name": "Hiring Manager",
            "message": f"{hm_summary}",
            "stance": hm_decision,
            "responding_to": "Contradiction Detector",
        })

    # If we got nothing, create a minimal debate
    if not debate:
        debate = [
            {"agent_name": "System", "message": "Agent analyses were incomplete. Scores derived from available data.", "stance": "hold", "responding_to": None}
        ]

    return debate


def _build_skill_gaps_from_analyses(state: dict) -> List[dict]:
    """Extract skill gaps from domain analysis when consensus doesn't provide them."""
    domain = state.get("domain_analysis", {})
    gaps = []

    domain_gaps = domain.get("domain_gaps", [])
    for gap in domain_gaps:
        gap_text = gap if isinstance(gap, str) else gap.get("gap", str(gap))
        gaps.append({
            "skill": gap_text.split("—")[0].strip() if "—" in gap_text else gap_text[:50],
            "current_level": "unknown",
            "required_level": "required by JD",
            "gap_severity": "medium",
            "training_estimate": "2-4 weeks",
        })

    # Also check technical weak areas
    technical = state.get("technical_analysis", {})
    for weak in technical.get("weak_areas", []):
        weak_text = weak if isinstance(weak, str) else str(weak)
        gaps.append({
            "skill": weak_text.split("—")[0].strip() if "—" in weak_text else weak_text[:50],
            "current_level": "below expectations",
            "required_level": "proficient",
            "gap_severity": "medium",
            "training_estimate": "2-3 weeks",
        })

    return gaps[:10]  # Limit to 10


def _build_why_not_hire_from_analyses(state: dict) -> dict:
    """Build why-not-hire data from individual analyses."""
    technical = state.get("technical_analysis", {})
    behavioral = state.get("behavioral_analysis", {})
    domain = state.get("domain_analysis", {})
    contradiction = state.get("contradiction_analysis", {})

    weaknesses = []
    evidence = []

    for w in technical.get("weak_areas", []):
        weaknesses.append(w if isinstance(w, str) else str(w))
    for c in behavioral.get("concern_indicators", []):
        weaknesses.append(c if isinstance(c, str) else str(c))
    for g in domain.get("domain_gaps", []):
        weaknesses.append(g if isinstance(g, str) else str(g))

    for c in contradiction.get("contradictions", []):
        if isinstance(c, dict):
            evidence.append(f"{c.get('claim', '')} vs {c.get('evidence', '')}")
        else:
            evidence.append(str(c))

    for flag in contradiction.get("red_flags", []):
        evidence.append(flag if isinstance(flag, str) else str(flag))

    if not weaknesses:
        weaknesses = ["Insufficient evidence to make a strong hiring case"]
    if not evidence:
        evidence = ["Limited interview data available for thorough assessment"]

    return {
        "major_weaknesses": weaknesses[:5],
        "evidence": evidence[:5],
        "risk_justification": f"Based on agent analyses: Technical ({technical.get('decision', 'unknown')}), "
                              f"Behavioral ({behavioral.get('decision', 'unknown')}), Domain ({domain.get('decision', 'unknown')})",
        "improvement_suggestions": [
            "Focus on strengthening areas identified as weak by technical analysis",
            "Practice behavioral interview responses using STAR method",
            "Expand domain knowledge in areas required by the job description",
        ],
        "thirty_day_plan": [
            "Week 1: Address immediate technical gaps",
            "Week 2: Build domain-specific knowledge",
            "Week 3: Practice communication and presentation",
            "Week 4: Mock interviews and self-assessment",
        ],
    }


def _build_improvement_roadmap_from_analyses(state: dict) -> dict:
    """Build improvement roadmap from analyses."""
    technical = state.get("technical_analysis", {})
    domain = state.get("domain_analysis", {})
    behavioral = state.get("behavioral_analysis", {})

    weak_areas = technical.get("weak_areas", [])
    domain_gaps = domain.get("domain_gaps", [])
    concerns = behavioral.get("concern_indicators", [])

    def _to_str(items):
        return [i if isinstance(i, str) else str(i) for i in items]

    week1 = _to_str(weak_areas[:2]) if weak_areas else ["Review core technical fundamentals"]
    week2 = _to_str(domain_gaps[:2]) if domain_gaps else ["Study domain-specific concepts from JD"]
    week3 = _to_str(concerns[:2]) if concerns else ["Practice communication and behavioral skills"]
    week4 = ["Conduct mock interviews", "Self-assess progress across all areas"]

    resources = []
    for area in (weak_areas + domain_gaps)[:3]:
        area_str = area if isinstance(area, str) else str(area)
        skill_name = area_str.split("—")[0].strip() if "—" in area_str else area_str[:40]
        resources.append(f"Study material for: {skill_name}")

    return {
        "week_1": week1,
        "week_2": week2,
        "week_3": week3,
        "week_4": week4,
        "resources": resources if resources else ["General interview preparation guides"],
    }


def _build_risk_analysis_from_analyses(state: dict, risk_score: int, learning: int, confidence: int) -> dict:
    """Build risk analysis from individual agent data."""
    contradiction = state.get("contradiction_analysis", {})
    hiring_mgr = state.get("hiring_manager_analysis", {})
    technical = state.get("technical_analysis", {})

    risk_factors = []
    mitigating = []

    # From contradiction detector
    for flag in contradiction.get("red_flags", []):
        risk_factors.append(flag if isinstance(flag, str) else str(flag))
    for c in contradiction.get("contradictions", []):
        if isinstance(c, dict) and c.get("severity") in ("high", "critical"):
            risk_factors.append(f"[{c.get('severity', 'high')}] {c.get('explanation', c.get('claim', ''))}")

    # From hiring manager
    for concern in hiring_mgr.get("key_concerns", []):
        risk_factors.append(concern if isinstance(concern, str) else str(concern))

    # Mitigating factors from strengths
    for s in technical.get("strong_areas", []):
        mitigating.append(s if isinstance(s, str) else str(s))
    for s in hiring_mgr.get("key_selling_points", []):
        mitigating.append(s if isinstance(s, str) else str(s))

    if not risk_factors:
        risk_factors = ["Limited interview data makes thorough risk assessment difficult"]
    if not mitigating:
        mitigating = ["Candidate submitted application and completed interview process"]

    return {
        "hiring_risk_score": risk_score,
        "learning_potential_score": learning,
        "attrition_risk": max(10, min(90, risk_score - 10)),
        "confidence_percentage": confidence,
        "risk_factors": risk_factors[:5],
        "mitigating_factors": mitigating[:5],
    }


def _extract_fallback_scores(state: dict) -> dict:
    """Extract scores from individual agents when consensus fails or is incomplete.
    Now builds FULL rich data from individual agent analyses instead of returning empties."""
    technical = state.get("technical_analysis", {})
    behavioral = state.get("behavioral_analysis", {})
    domain = state.get("domain_analysis", {})
    hiring_mgr = state.get("hiring_manager_analysis", {})
    contradiction = state.get("contradiction_analysis", {})

    logger.info(f"Fallback extraction — technical keys: {list(technical.keys())}")
    logger.info(f"Fallback extraction — behavioral keys: {list(behavioral.keys())}")
    logger.info(f"Fallback extraction — domain keys: {list(domain.keys())}")
    logger.info(f"Fallback extraction — hiring_mgr keys: {list(hiring_mgr.keys())}")

    # Assess transcript quality to set appropriate defaults
    transcript_quality = _assess_transcript_quality(state)
    if transcript_quality in ("very_poor", "no_answers", "no_transcript"):
        default_score = 15
        default_risk = 70
    elif transcript_quality == "poor":
        default_score = 25
        default_risk = 55
    else:
        default_score = 30
        default_risk = 45

    logger.info(f"Fallback: transcript_quality={transcript_quality}, default_score={default_score}")

    # Extract scores with multiple key fallbacks
    tech_score = _safe_score(
        technical.get("technical_score")
        or technical.get("overall_score")
        or technical.get("score"), default_score)
    behavior_score = _safe_score(
        behavioral.get("behavior_score")
        or behavioral.get("behavioral_score")
        or behavioral.get("overall_score"), default_score)
    domain_score = _safe_score(
        domain.get("domain_score")
        or domain.get("overall_score"), default_score)
    communication_score = _safe_score(
        behavioral.get("communication_clarity")
        or behavioral.get("communication_score"), default_score)
    learning_potential = _safe_score(
        behavioral.get("growth_mindset")
        or behavioral.get("learning_potential"), default_score)
    risk_score = _safe_score(
        contradiction.get("consistency_score")
        or hiring_mgr.get("risk_score"), default_risk)
    if contradiction.get("consistency_score"):
        risk_score = 100 - risk_score

    decisions = []
    for analysis in [technical, behavioral, domain, hiring_mgr, contradiction]:
        d = analysis.get("decision", "")
        if d:
            decisions.append(d.lower().strip())

    resume_analysis = state.get("resume_analysis", {})
    d = resume_analysis.get("decision", "")
    if d:
        decisions.append(d.lower().strip())

    strong_hire = sum(1 for d in decisions if "strong" in d and "hire" in d)
    hire_count = sum(1 for d in decisions if "hire" in d and "strong" not in d and "no" not in d and "not" not in d)
    reject_count = sum(1 for d in decisions if "reject" in d or "no hire" in d or "no_hire" in d or "not" in d)
    hold_count = sum(1 for d in decisions if "hold" in d or "conditional" in d)

    if strong_hire >= 2:
        final = "Strong Hire"
    elif hire_count + strong_hire > reject_count + hold_count:
        final = "Hire"
    elif reject_count > hire_count + strong_hire:
        final = "Reject"
    else:
        final = "Hold"

    confidences = []
    for analysis in [technical, behavioral, domain, hiring_mgr, contradiction, resume_analysis]:
        c = analysis.get("confidence")
        if c is not None:
            confidences.append(_safe_score(c, 30))
    confidence = int(sum(confidences) / len(confidences)) if confidences else (25 if transcript_quality in ('very_poor', 'no_answers') else 40)

    logger.info(f"Fallback scores: tech={tech_score}, behavior={behavior_score}, "
                f"domain={domain_score}, comm={communication_score}, learning={learning_potential}")

    # Build rich structured data from individual agent analyses
    agent_debate = _build_agent_debate_from_analyses(state)
    skill_gaps = _build_skill_gaps_from_analyses(state)
    contradictions_data = contradiction.get("contradictions", [])
    why_not_hire = _build_why_not_hire_from_analyses(state) if final in ("Hold", "Reject") else None
    improvement_roadmap = _build_improvement_roadmap_from_analyses(state)
    risk_analysis = _build_risk_analysis_from_analyses(state, risk_score, learning_potential, confidence)

    # Build reasoning from agent summaries
    reasoning_parts = []
    if technical.get("summary"):
        reasoning_parts.append(f"TECHNICAL ASSESSMENT: {technical['summary']}")
    if behavioral.get("summary"):
        reasoning_parts.append(f"BEHAVIORAL ASSESSMENT: {behavioral['summary']}")
    if domain.get("summary"):
        reasoning_parts.append(f"DOMAIN FIT: {domain['summary']}")
    if contradiction.get("summary"):
        reasoning_parts.append(f"CREDIBILITY CHECK: {contradiction['summary']}")
    if hiring_mgr.get("summary"):
        reasoning_parts.append(f"BUSINESS FIT: {hiring_mgr['summary']}")
    reasoning_parts.append(f"FINAL VERDICT: {final} with {confidence}% confidence based on weighted agent scores.")

    reasoning = "\n\n".join(reasoning_parts) if reasoning_parts else "Evaluation based on available data from individual agent analyses."

    # Build agent opinions from individual analyses
    agent_opinions = []
    for name, analysis in [
        ("Resume Analyst", resume_analysis),
        ("Technical Depth Analyst", technical),
        ("Behavioral Psychologist", behavioral),
        ("Domain Expert", domain),
        ("Hiring Manager", hiring_mgr),
    ]:
        if analysis and isinstance(analysis, dict) and not analysis.get("error"):
            agent_opinions.append({
                "agent_name": name,
                "role": name,
                "decision": analysis.get("decision", "conditional"),
                "confidence": _safe_score(analysis.get("confidence"), 40),
                "reasoning": analysis.get("summary", analysis.get("decision_reasoning", "")),
                "key_concerns": analysis.get("weak_areas", analysis.get("concern_indicators", analysis.get("domain_gaps", [])))[:3],
                "key_strengths": analysis.get("strong_areas", analysis.get("positive_indicators", analysis.get("domain_strengths", [])))[:3],
            })

    return {
        "technical_score": tech_score,
        "behavior_score": behavior_score,
        "domain_score": domain_score,
        "communication_score": communication_score,
        "risk_score": risk_score,
        "learning_potential": learning_potential,
        "confidence": confidence,
        "final_decision": final,
        "reasoning": reasoning,
        "agent_debate": agent_debate,
        "skill_gaps": skill_gaps,
        "contradictions": contradictions_data,
        "risk_analysis": risk_analysis,
        "why_not_hire": why_not_hire,
        "improvement_roadmap": improvement_roadmap,
        "agent_opinions": agent_opinions,
    }


def _validate_and_merge_scores(consensus: dict, state: dict) -> dict:
    """Validate consensus scores and merge from individual agents if any are 0.
    Also backfills rich data fields (debate, skill_gaps, etc.) from fallback."""
    fallback = _extract_fallback_scores(state)

    score_keys = ["technical_score", "behavior_score", "domain_score",
                  "communication_score", "learning_potential"]
    all_zero = all(consensus.get(k, 0) == 0 for k in score_keys)

    if all_zero:
        logger.warning("Consensus returned all-zero scores, merging from individual agents")
        for key in score_keys + ["risk_score", "confidence"]:
            if consensus.get(key, 0) == 0 and fallback.get(key, 0) > 0:
                consensus[key] = fallback[key]

    for key in score_keys + ["risk_score", "confidence"]:
        consensus[key] = _safe_score(consensus.get(key), fallback.get(key, 30))

    if not consensus.get("final_decision") or consensus["final_decision"] == "Pending":
        consensus["final_decision"] = fallback["final_decision"]

    # Backfill ALL rich data fields from fallback if consensus is missing them
    rich_fields = ["risk_analysis", "contradictions", "agent_debate", "skill_gaps",
                   "why_not_hire", "improvement_roadmap", "agent_opinions", "reasoning"]
    for field in rich_fields:
        current = consensus.get(field)
        if not current or (isinstance(current, list) and len(current) == 0):
            fb_val = fallback.get(field)
            if fb_val:
                consensus[field] = fb_val
                logger.info(f"Backfilled '{field}' from fallback ({type(fb_val).__name__})")

    return consensus


def _normalize_decision(decision: str) -> str:
    """Normalize any decision string to one of: Strong Hire, Hire, Hold, Reject."""
    d = decision.lower().strip()
    if "strong" in d and "hire" in d:
        return "Strong Hire"
    if ("hire" in d) and ("no" not in d) and ("not" not in d) and ("reject" not in d):
        return "Hire"
    if "hold" in d or "conditional" in d:
        return "Hold"
    if "reject" in d or "no hire" in d or "no_hire" in d or "not hire" in d:
        return "Reject"
    # Default to Hold for any ambiguous decision
    return "Hold"


def _save_evaluation(state: dict, candidate, db: AsyncSession) -> Evaluation:
    """Create Evaluation and AgentLog records from final state."""
    consensus = state.get("consensus", {})

    if not consensus or not consensus.get("final_decision") or consensus.get("final_decision") == "Pending":
        logger.info("Consensus missing or pending — using full fallback scores")
        consensus = _extract_fallback_scores(state)
    else:
        logger.info(f"Consensus has decision: {consensus.get('final_decision')} — validating scores")
        consensus = _validate_and_merge_scores(consensus, state)

    state["consensus"] = consensus

    # Normalize decision
    raw_decision = consensus.get("final_decision", "Pending")
    normalized_decision = _normalize_decision(raw_decision) if raw_decision != "Pending" else "Hold"
    consensus["final_decision"] = normalized_decision

    evaluation = Evaluation(
        candidate_id=candidate.id,
        technical_score=consensus.get("technical_score", 0),
        behavior_score=consensus.get("behavior_score", 0),
        risk_score=consensus.get("risk_score", 0),
        learning_potential=consensus.get("learning_potential", 0),
        confidence=consensus.get("confidence", 0),
        domain_score=consensus.get("domain_score", 0),
        communication_score=consensus.get("communication_score", 0),
        final_decision=consensus.get("final_decision", "Pending"),
        reasoning=consensus.get("reasoning", ""),
        scores_json={
            "technical_score": consensus.get("technical_score", 0),
            "behavior_score": consensus.get("behavior_score", 0),
            "risk_score": consensus.get("risk_score", 0),
            "learning_potential": consensus.get("learning_potential", 0),
            "domain_score": consensus.get("domain_score", 0),
            "communication_score": consensus.get("communication_score", 0),
            "agent_opinions": consensus.get("agent_opinions", []),
        },
        skill_gaps=consensus.get("skill_gaps"),
        contradictions=consensus.get("contradictions"),
        why_not_hire=consensus.get("why_not_hire"),
        improvement_roadmap=consensus.get("improvement_roadmap"),
        agent_debate=consensus.get("agent_debate"),
        risk_analysis=consensus.get("risk_analysis"),
    )
    db.add(evaluation)

    for log in state.get("agent_logs", []):
        db.add(AgentLog(
            candidate_id=candidate.id,
            agent_name=log["agent_name"],
            message=log["message"],
            agent_role=log.get("agent_role"),
            phase=log.get("phase"),
            timestamp=datetime.now(timezone.utc),
        ))

    return evaluation


class EvaluationService:
    """Orchestrates candidate evaluation through the multi-agent pipeline."""

    async def run_evaluation(self, candidate_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Run the full hiring panel evaluation for a candidate (blocking)."""

        result = await db.execute(
            select(Candidate).where(Candidate.id == uuid_mod.UUID(candidate_id))
        )
        candidate = result.scalar_one_or_none()
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")

        candidate.status = "evaluating"
        await db.flush()

        try:
            # Vector store (optional)
            try:
                vs = get_vector_store()
                if vs:
                    await vs.store_resume(candidate_id, candidate.resume_text)
                    await vs.store_transcript(candidate_id, candidate.transcript_text)
                    await vs.store_job_description(candidate_id, candidate.job_description)
            except Exception:
                logger.warning("Vector store operation failed", exc_info=True)

            initial_state = _build_initial_state(candidate, candidate_id)

            # Run full pipeline
            final_state = await hiring_graph.ainvoke(initial_state)

            # Save with validation
            evaluation = _save_evaluation(final_state, candidate, db)
            candidate.status = "completed"
            await db.flush()
            await db.refresh(evaluation)

            consensus = final_state.get("consensus", {})
            try:
                await cache_service.cache_evaluation(candidate_id, {
                    "final_decision": consensus.get("final_decision"),
                    "confidence": consensus.get("confidence"),
                    "technical_score": consensus.get("technical_score"),
                })
            except Exception:
                logger.warning("Cache write failed", exc_info=True)

            return {
                "candidate_id": candidate_id,
                "evaluation_id": str(evaluation.id),
                "status": "completed",
                "final_decision": consensus.get("final_decision", "Pending"),
                "confidence": consensus.get("confidence", 0),
            }

        except Exception as e:
            candidate.status = "failed"
            await db.flush()
            raise e

    async def run_evaluation_stream(
        self, candidate_id: str, db: AsyncSession
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Run evaluation with streaming agent events via SSE."""

        # Fetch candidate
        result = await db.execute(
            select(Candidate).where(Candidate.id == uuid_mod.UUID(candidate_id))
        )
        candidate = result.scalar_one_or_none()
        if not candidate:
            yield {"type": "error", "message": "Candidate not found"}
            return

        if candidate.status == "evaluating":
            yield {"type": "error", "message": "Evaluation already in progress"}
            return

        candidate.status = "evaluating"
        await db.flush()

        yield {
            "type": "status",
            "message": "Initializing evaluation pipeline...",
            "step": 0,
            "total_steps": len(AGENT_PIPELINE),
        }

        # Vector store (optional)
        try:
            vs = get_vector_store()
            if vs:
                await vs.store_resume(candidate_id, candidate.resume_text)
                await vs.store_transcript(candidate_id, candidate.transcript_text)
                await vs.store_job_description(candidate_id, candidate.job_description)
        except Exception:
            logger.warning("Vector store operation failed during stream", exc_info=True)

        state = _build_initial_state(candidate, candidate_id)
        total = len(AGENT_PIPELINE)

        try:
            for i, step in enumerate(AGENT_PIPELINE):
                # Emit agent starting
                yield {
                    "type": "agent_start",
                    "step": i + 1,
                    "total_steps": total,
                    "agent_name": step["name"],
                    "message": step["description"],
                }

                prev_log_count = len(state.get("agent_logs", []))

                # Run the agent
                state = await step["agent"].invoke(state)

                # Emit new agent logs
                new_logs = state.get("agent_logs", [])[prev_log_count:]
                for log in new_logs:
                    yield {
                        "type": "agent_message",
                        "agent_name": log.get("agent_name", step["name"]),
                        "message": log.get("message", "Analysis completed."),
                        "phase": log.get("phase", "analysis"),
                        "role": log.get("agent_role", ""),
                    }

                # If consensus agent, also emit scores and debate messages
                if step["name"] == "Consensus Negotiator":
                    consensus = state.get("consensus", {})
                    # If consensus failed or is empty, use full fallback
                    if not consensus or not isinstance(consensus, dict) or consensus.get("error") or not consensus.get("final_decision"):
                        logger.warning("Consensus agent produced empty/error result, using full fallback")
                        consensus = _extract_fallback_scores(state)
                        state["consensus"] = consensus
                    else:
                        consensus = _validate_and_merge_scores(consensus, state)
                        state["consensus"] = consensus

                    yield {
                        "type": "scores",
                        "data": {
                            "technical_score": consensus.get("technical_score", 0),
                            "behavior_score": consensus.get("behavior_score", 0),
                            "risk_score": consensus.get("risk_score", 0),
                            "learning_potential": consensus.get("learning_potential", 0),
                            "domain_score": consensus.get("domain_score", 0),
                            "communication_score": consensus.get("communication_score", 0),
                            "confidence": consensus.get("confidence", 0),
                            "final_decision": consensus.get("final_decision", "Pending"),
                        },
                    }

                    debate = consensus.get("agent_debate", [])
                    if isinstance(debate, list):
                        for msg in debate:
                            yield {
                                "type": "debate_message",
                                "data": msg if isinstance(msg, dict) else {"message": str(msg)},
                            }

                yield {
                    "type": "agent_complete",
                    "step": i + 1,
                    "total_steps": total,
                    "agent_name": step["name"],
                }

            # Add final report log
            state["agent_logs"].append({
                "agent_name": "System",
                "agent_role": "Orchestrator",
                "message": f"Evaluation complete. Decision: {state.get('consensus', {}).get('final_decision', 'Unknown')} "
                           f"with {state.get('consensus', {}).get('confidence', 0)}% confidence.",
                "phase": "final",
            })

            # Save to DB and commit immediately
            evaluation = _save_evaluation(state, candidate, db)
            candidate.status = "completed"
            await db.flush()
            await db.commit()
            await db.refresh(evaluation)

            try:
                consensus = state.get("consensus", {})
                await cache_service.cache_evaluation(candidate_id, {
                    "final_decision": consensus.get("final_decision"),
                    "confidence": consensus.get("confidence"),
                    "technical_score": consensus.get("technical_score"),
                })
            except Exception:
                logger.warning("Cache write failed during stream", exc_info=True)

            yield {
                "type": "complete",
                "evaluation_id": str(evaluation.id),
                "candidate_id": candidate_id,
                "final_decision": state.get("consensus", {}).get("final_decision", "Pending"),
                "confidence": state.get("consensus", {}).get("confidence", 0),
            }

        except Exception as e:
            candidate.status = "failed"
            await db.flush()
            logger.error(f"Evaluation stream failed: {e}", exc_info=True)
            yield {"type": "error", "message": str(e)}


# Singleton
evaluation_service = EvaluationService()
