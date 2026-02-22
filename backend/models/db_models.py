"""SQLAlchemy ORM models for the Verdexa database."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Float, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from db.database import Base


class Candidate(Base):
    """Candidate profile with uploaded documents."""
    __tablename__ = "candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    resume_text = Column(Text, nullable=False)
    transcript_text = Column(Text, nullable=False)
    job_description = Column(Text, nullable=False)
    github_repo_url = Column(String(500), nullable=True)
    repo_project_id = Column(UUID(as_uuid=True), nullable=True)  # Links to Supabase projects table
    status = Column(String(20), default="pending")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    evaluations = relationship("Evaluation", back_populates="candidate", cascade="all, delete-orphan")
    agent_logs = relationship("AgentLog", back_populates="candidate", cascade="all, delete-orphan")


class Evaluation(Base):
    """Evaluation results for a candidate."""
    __tablename__ = "evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)

    # Scores
    technical_score = Column(Float, default=0.0)
    behavior_score = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)
    learning_potential = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    domain_score = Column(Float, default=0.0)
    communication_score = Column(Float, default=0.0)

    # Security Intelligence
    security_intelligence_index = Column(Float, default=0.0)
    skill_inflation_score = Column(Float, default=0.0)
    skill_inflation_verdict = Column(String(50), nullable=True)

    # Decision
    final_decision = Column(String(50), default="Pending")  # Hire / No Hire / Conditional
    reasoning = Column(Text, nullable=True)

    # Detailed JSON data
    scores_json = Column(JSON, nullable=True)
    skill_gaps = Column(JSON, nullable=True)
    contradictions = Column(JSON, nullable=True)
    why_not_hire = Column(JSON, nullable=True)
    improvement_roadmap = Column(JSON, nullable=True)
    agent_debate = Column(JSON, nullable=True)
    risk_analysis = Column(JSON, nullable=True)
    skill_inflation_data = Column(JSON, nullable=True)
    security_intelligence_data = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    candidate = relationship("Candidate", back_populates="evaluations")


class AgentLog(Base):
    """Individual agent reasoning logs."""
    __tablename__ = "agent_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)
    agent_name = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    agent_role = Column(String(100), nullable=True)
    phase = Column(String(50), nullable=True)  # analysis, debate, consensus
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    candidate = relationship("Candidate", back_populates="agent_logs")


class RepoAnalysisResult(Base):
    """Links a candidate's repo scan to their evaluation."""
    __tablename__ = "repo_analysis_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), nullable=True)
    project_id = Column(UUID(as_uuid=True), nullable=False)  # Supabase projects.id
    security_intelligence_index = Column(Float, default=0.0)
    security_intelligence_data = Column(JSON, nullable=True)
    skill_inflation_score = Column(Float, default=0.0)
    skill_inflation_data = Column(JSON, nullable=True)
    total_vulnerabilities = Column(Float, default=0)
    critical_count = Column(Float, default=0)
    high_count = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SecurityReport(Base):
    """Stored security report from a completed scan."""
    __tablename__ = "security_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), nullable=False)
    report_data = Column(JSON, nullable=True)
    executive_summary = Column(Text, nullable=True)
    overall_risk_rating = Column(String(20), nullable=True)
    overall_risk_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
