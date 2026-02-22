"""Pydantic schemas for API request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime
from uuid import UUID

AgentState = Dict[str, Any]


# ──────────────────── API Response ────────────────────

class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    
    class Config:
        from_attributes = True


# ──────────────────── Candidate Schemas ────────────────────

class CandidateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = None
    resume_text: str = Field(..., min_length=10)
    transcript_text: Optional[str] = ""
    job_description: str = Field(..., min_length=10)


class CandidateResponse(BaseModel):
    id: UUID
    name: str
    email: Optional[str]
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class CandidateDetail(CandidateResponse):
    resume_text: str
    transcript_text: str
    job_description: str

    class Config:
        from_attributes = True


# ──────────────────── Score Schemas ────────────────────

class SkillGap(BaseModel):
    skill: str
    current_level: str
    required_level: str
    gap_severity: str  # low, medium, high
    training_estimate: str


class Contradiction(BaseModel):
    claim: str
    evidence: str
    severity: str  # low, medium, high, critical
    explanation: str


class AgentOpinion(BaseModel):
    agent_name: str
    role: str
    decision: str  # hire, no_hire, conditional
    confidence: float
    reasoning: str
    key_concerns: List[str] = []
    key_strengths: List[str] = []


class DebateMessage(BaseModel):
    agent_name: str
    message: str
    stance: str
    responding_to: Optional[str] = None
    timestamp: Optional[str] = None


class WhyNotHire(BaseModel):
    major_weaknesses: List[str]
    evidence: List[str]
    risk_justification: str
    improvement_suggestions: List[str]
    thirty_day_plan: Optional[List[str]] = None


class RiskAnalysis(BaseModel):
    hiring_risk_score: float
    learning_potential_score: float
    attrition_risk: float
    confidence_percentage: float
    risk_factors: List[str]
    mitigating_factors: List[str]


class ImprovementRoadmap(BaseModel):
    week_1: List[str]
    week_2: List[str]
    week_3: List[str]
    week_4: List[str]
    resources: List[str]


# ──────────────────── Evaluation Schemas ────────────────────

class EvaluationResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    technical_score: float
    behavior_score: float
    risk_score: float
    learning_potential: float
    confidence: float
    domain_score: float
    communication_score: float
    final_decision: str
    reasoning: Optional[str]
    scores_json: Optional[dict]
    skill_gaps: Optional[List[SkillGap]]
    contradictions: Optional[List[Contradiction]]
    why_not_hire: Optional[WhyNotHire]
    improvement_roadmap: Optional[ImprovementRoadmap]
    agent_debate: Optional[List[DebateMessage]]
    risk_analysis: Optional[RiskAnalysis]
    created_at: datetime

    class Config:
        from_attributes = True


class EvaluationSummary(BaseModel):
    candidate_id: UUID
    candidate_name: str
    final_decision: str
    confidence: float
    technical_score: float
    risk_score: float
    created_at: datetime


# ──────────────────── Agent Log Schemas ────────────────────

class AgentLogResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    agent_name: str
    message: str
    agent_role: Optional[str]
    phase: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


# ──────────────────── Run Evaluation Request ────────────────────

class RunEvaluationRequest(BaseModel):
    candidate_id: UUID
