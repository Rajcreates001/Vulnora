
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class APIResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None


# ─── Enums ────────────────────────────────────────────

class SeverityLevel(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ScanStatus(str, Enum):
    PENDING = "pending"
    RECON = "recon"
    ANALYSIS = "analysis"
    EXPLOIT = "exploit"
    PATCH = "patch"
    REPORT = "report"
    COMPLETED = "completed"
    FAILED = "failed"


# ─── Project Models ───────────────────────────────────

class ProjectCreate(BaseModel):
    name: str
    repo_url: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    repo_path: Optional[str] = None
    scan_status: ScanStatus = ScanStatus.PENDING
    created_at: str
    file_count: int = 0
    vulnerability_count: int = 0


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int


# ─── File Models ──────────────────────────────────────

class FileInfo(BaseModel):
    id: str
    project_id: str
    file_path: str
    language: Optional[str] = None
    size: int = 0


# ─── Vulnerability Models ────────────────────────────

class VulnerabilityScore(BaseModel):
    severity: SeverityLevel
    risk_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=100)
    exploitability: float = Field(ge=0, le=100)
    impact: float = Field(ge=0, le=100)


class VulnerabilityResponse(BaseModel):
    id: str
    project_id: str
    title: str
    vulnerability_type: str
    severity: SeverityLevel
    description: str
    file_path: str
    line_start: int
    line_end: int
    vulnerable_code: str
    exploit: Optional[str] = None
    exploit_script: Optional[str] = None
    patch: Optional[str] = None
    patch_explanation: Optional[str] = None
    risk_score: float
    confidence: float
    exploitability: float
    impact: float
    cwe_id: Optional[str] = None
    cvss_vector: Optional[str] = None
    attack_path: Optional[List[Dict[str, Any]]] = None
    created_at: str


class VulnerabilityListResponse(BaseModel):
    vulnerabilities: List[VulnerabilityResponse]
    total: int
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0


# ─── Agent Log Models ────────────────────────────────

class AgentLogResponse(BaseModel):
    id: str
    project_id: str
    agent_name: str
    message: str
    log_type: str = "info"
    data: Optional[Dict[str, Any]] = None
    timestamp: str


class AgentLogListResponse(BaseModel):
    logs: List[AgentLogResponse]
    total: int


# ─── Scan Models ──────────────────────────────────────

class ScanStartRequest(BaseModel):
    project_id: str


class ScanStatusResponse(BaseModel):
    project_id: str
    status: ScanStatus
    current_agent: Optional[str] = None
    progress: float = 0.0
    agents_completed: List[str] = []
    message: Optional[str] = None


# ─── Report Models ────────────────────────────────────

class SecurityReport(BaseModel):
    project_id: str
    executive_summary: str
    total_vulnerabilities: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    overall_risk_score: float
    vulnerabilities: List[VulnerabilityResponse]
    attack_paths: List[Dict[str, Any]]
    recommendations: List[str]
    agent_logs: List[AgentLogResponse]
    generated_at: str


# ─── Attack Path Models ──────────────────────────────

class AttackPathNode(BaseModel):
    id: str
    label: str
    node_type: str  # entry_point, function, database, exploit_outcome
    data: Optional[Dict[str, Any]] = None


class AttackPathEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None


class AttackPathGraph(BaseModel):
    nodes: List[AttackPathNode]
    edges: List[AttackPathEdge]


# ─── LangGraph State ─────────────────────────────────

class AgentState(BaseModel):
    project_id: str
    files: List[Dict[str, Any]] = []
    recon_results: Optional[Dict[str, Any]] = None
    static_analysis_results: Optional[Dict[str, Any]] = None
    vulnerabilities: List[Dict[str, Any]] = []
    exploits: List[Dict[str, Any]] = []
    patches: List[Dict[str, Any]] = []
    risk_scores: List[Dict[str, Any]] = []
    debate_results: List[Dict[str, Any]] = []
    report: Optional[Dict[str, Any]] = None
    current_agent: str = ""
    logs: List[Dict[str, Any]] = []
    errors: List[str] = []
