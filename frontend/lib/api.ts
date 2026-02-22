/**
 * API client for communicating with the Verdexa backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ──────────────────── Types ────────────────────

export interface Candidate {
  id: string;
  name: string;
  email: string | null;
  status: string;
  created_at: string;
  updated_at: string | null;
}

export interface CandidateDetail extends Candidate {
  resume_text: string;
  transcript_text: string;
  job_description: string;
}

export interface SkillGap {
  skill: string;
  current_level: string;
  required_level: string;
  gap_severity: string;
  training_estimate: string;
}

export interface Contradiction {
  claim: string;
  evidence: string;
  severity: string;
  explanation: string;
}

export interface DebateMessage {
  agent_name: string;
  message: string;
  stance: string;
  responding_to: string | null;
  timestamp?: string;
}

export interface WhyNotHire {
  major_weaknesses: string[];
  evidence: string[];
  risk_justification: string;
  improvement_suggestions: string[];
  thirty_day_plan?: string[];
}

export interface RiskAnalysis {
  hiring_risk_score: number;
  learning_potential_score: number;
  attrition_risk: number;
  confidence_percentage: number;
  risk_factors: string[];
  mitigating_factors: string[];
}

export interface ImprovementRoadmap {
  week_1: string[];
  week_2: string[];
  week_3: string[];
  week_4: string[];
  resources: string[];
}

export interface Evaluation {
  id: string;
  candidate_id: string;
  technical_score: number;
  behavior_score: number;
  risk_score: number;
  learning_potential: number;
  confidence: number;
  domain_score: number;
  communication_score: number;
  final_decision: string;
  reasoning: string | null;
  scores_json: Record<string, number> | null;
  skill_gaps: SkillGap[] | null;
  contradictions: Contradiction[] | null;
  why_not_hire: WhyNotHire | null;
  improvement_roadmap: ImprovementRoadmap | null;
  agent_debate: DebateMessage[] | null;
  risk_analysis: RiskAnalysis | null;
  created_at: string;
}

export interface AgentLog {
  id: string;
  candidate_id: string;
  agent_name: string;
  message: string;
  agent_role: string | null;
  phase: string | null;
  timestamp: string;
}

export interface EvaluationSummary {
  candidate_id: string;
  candidate_name: string;
  final_decision: string;
  confidence: number;
  technical_score: number;
  risk_score: number;
  created_at: string;
}

// Interview types
export interface InterviewQuestion {
  id?: number;
  text: string;
  category: string;
  difficulty: string;
  evaluating?: string;
  key_points?: string[];
  follow_up_topics?: string[];
}

export interface InterviewSession {
  session_id: string;
  candidate_id: string;
  status: string;
  duration_minutes: number;
  current_question: InterviewQuestion;
  total_questions: number;
  started_at: string;
  remaining_seconds?: number;
}

export interface AnswerResponse {
  session_id: string;
  reply: {
    text: string;
    category: string;
  } | null;
  next_question: InterviewQuestion | null;
  answer_assessment: {
    quality: string;
    score: number;
    key_points_hit?: string[];
    missed_points?: string[];
    note: string;
  };
  current_question_index: number;
  total_questions_asked: number;
  time_expired?: boolean;
  remaining_seconds?: number;
}

export interface TranscriptEntry {
  speaker: string;
  text: string;
  timestamp: string;
  type: string;
  question_index?: number;
}

export interface ResumeData {
  name: string;
  email: string;
  phone?: string;
  location?: string;
  summary?: string;
  experience_years?: number;
  skills: {
    technical: string[];
    soft: string[];
    tools: string[];
  };
  experience: Array<{
    company: string;
    role: string;
    duration: string;
    highlights: string[];
  }>;
  education: Array<{
    institution: string;
    degree: string;
    year: string;
  }>;
  projects: Array<{
    name: string;
    description: string;
    technologies: string[];
  }>;
  certifications: string[];
  complexity_level: string;
}

// ──────────────────── API Functions ────────────────────

async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    const detail = error.detail;
    const message = Array.isArray(detail)
      ? detail.map((d: any) => d.msg || JSON.stringify(d)).join("; ")
      : (typeof detail === "string" ? detail : `API Error: ${response.status}`);
    throw new Error(message);
  }

  return response.json();
}

async function apiRequestWithErrorHandling<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  try {
    return await apiRequest<T>(endpoint, options);
  } catch (err: any) {
    const msg = err?.message || String(err);
    if (msg === "Failed to fetch" || msg.includes("fetch") || msg.includes("network")) {
      throw new Error(
        `Cannot reach API at ${API_BASE}. Ensure the backend is running and CORS allows ${typeof window !== "undefined" ? window.location.origin : "your origin"}.`
      );
    }
    throw err;
  }
}

// Candidates (use error handling for upload to give clearer "failed to fetch" message)
export async function uploadCandidate(data: {
  name: string;
  email?: string;
  resume_text: string;
  transcript_text?: string;
  job_description: string;
}): Promise<Candidate> {
  return apiRequestWithErrorHandling<Candidate>("/api/upload-candidate", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function uploadCandidateWithFile(formData: FormData): Promise<Candidate> {
  const url = `${API_BASE}/api/upload-candidate-files`;
  try {
  const response = await fetch(url, {
    method: "POST",
    body: formData,
    // Don't set Content-Type for FormData — browser sets boundary
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    const detail = error.detail;
    const message = Array.isArray(detail)
      ? detail.map((d: any) => d.msg || JSON.stringify(d)).join("; ")
      : (typeof detail === "string" ? detail : `Upload failed: ${response.status}`);
    throw new Error(message);
  }
  return response.json();
  } catch (err: any) {
    const msg = err?.message || String(err);
    if (msg === "Failed to fetch" || msg.includes("fetch") || msg.includes("network")) {
      throw new Error(
        `Cannot reach API at ${API_BASE}. Ensure the backend is running and CORS is configured.`
      );
    }
    throw err;
  }
}

export async function listCandidates(): Promise<Candidate[]> {
  return apiRequest<Candidate[]>("/api/candidates");
}

export async function getCandidate(id: string): Promise<CandidateDetail> {
  return apiRequest<CandidateDetail>(`/api/candidates/${id}`);
}

export async function deleteCandidate(id: string): Promise<void> {
  return apiRequest(`/api/candidates/${id}`, { method: "DELETE" });
}

export async function resetCandidateStatus(id: string): Promise<void> {
  return apiRequest(`/api/candidates/${id}/reset`, { method: "PATCH" });
}

// Evaluations
export async function runEvaluation(candidateId: string): Promise<{
  candidate_id: string;
  evaluation_id: string;
  status: string;
  final_decision: string;
  confidence: number;
}> {
  return apiRequest("/api/run-evaluation", {
    method: "POST",
    body: JSON.stringify({ candidate_id: candidateId }),
  });
}

export async function getResults(candidateId: string): Promise<any> {
  return apiRequest<any>(`/api/evaluation-results/${candidateId}`);
}

/** Scan results for a project (code security scan). */
export async function getScanResults(projectId: string): Promise<any> {
  const res = await apiRequest<any>(`/api/results/${projectId}`);
  return res.data || res;
}

export async function listEvaluations(): Promise<EvaluationSummary[]> {
  return apiRequest<EvaluationSummary[]>("/api/evaluations");
}

// Agent Logs (candidates - hiring evaluation)
export async function getAgentLogs(candidateId: string): Promise<AgentLog[]> {
  return apiRequest<AgentLog[]>(`/api/agent-logs/${candidateId}`);
}

/** Agent logs for project (code security scan). */
export async function getProjectAgentLogs(projectId: string): Promise<any[]> {
  const res = await apiRequest<any>(`/api/project-logs/${projectId}`);
  const data = (res as any)?.data;
  const logs = data?.logs ?? data ?? [];
  return Array.isArray(logs) ? logs : [];
}

// Projects (Security Scan)
export async function getProject(projectId: string): Promise<any> {
  const res = await apiRequest<any>(`/api/projects/${projectId}`);
  return res.data || res;
}

export async function deleteProject(projectId: string): Promise<void> {
  await apiRequest(`/api/projects/${projectId}`, { method: "DELETE" });
}

// Interview
export async function startInterview(
  candidateId: string,
  durationMinutes: number = 15,
  inPersonTranscript?: string,
): Promise<InterviewSession> {
  return apiRequest<InterviewSession>("/api/interview/start", {
    method: "POST",
    body: JSON.stringify({
      candidate_id: candidateId,
      duration_minutes: durationMinutes,
      in_person_transcript: inPersonTranscript || null,
    }),
  });
}

export async function submitAnswer(
  sessionId: string,
  answerText: string,
  emotionData?: Record<string, any>,
): Promise<AnswerResponse> {
  return apiRequest<AnswerResponse>("/api/interview/answer", {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      answer_text: answerText,
      emotion_data: emotionData || null,
    }),
  });
}

export async function endInterview(sessionId: string): Promise<any> {
  return apiRequest(`/api/interview/end/${sessionId}`, { method: "POST" });
}

export async function getInterviewSession(sessionId: string): Promise<any> {
  return apiRequest(`/api/interview/session/${sessionId}`);
}

export function getEvaluationStreamUrl(candidateId: string): string {
  return `${API_BASE}/api/run-evaluation-stream/${candidateId}`;
}

export function getEndAndEvaluateStreamUrl(sessionId: string): string {
  return `${API_BASE}/api/interview/end-and-evaluate/${sessionId}`;
}

// Resume extraction
export async function extractResumeData(resumeText: string): Promise<ResumeData> {
  return apiRequest<ResumeData>("/api/resume/extract", {
    method: "POST",
    body: JSON.stringify({ resume_text: resumeText }),
  });
}

// ──────────────────── Security Scan Types ────────────────────

export interface Project {
  id: string;
  name: string;
  repo_path: string | null;
  scan_status: string;
  created_at: string;
}

export interface ScanStatus {
  project_id: string;
  status: string;
  current_agent: string;
  progress: number;
  agents_completed: string[];
  message: string;
}

export interface SecurityIntelligence {
  security_intelligence_index: number;
  breakdown: {
    exploitability: number;
    patch_quality: number;
    secure_coding: number;
    complexity: number;
    risk_awareness: number;
    documentation: number;
  };
  summary: string;
  total_vulnerabilities: number;
  critical_count: number;
  high_count: number;
  files_analyzed: number;
}

export interface SkillInflation {
  skill_inflation_score: number;
  verdict: string;
  contradictions: Array<{
    claim: string;
    evidence: string;
    severity: string;
    explanation: string;
    matching_vulnerabilities?: Array<{
      vulnerability: string;
      type: string;
      severity: string;
      file: string;
    }>;
  }>;
  total_contradictions: number;
  summary: string;
}

// ──────────────────── Security Scan API Functions ────────────────────

export async function listProjects(): Promise<Project[]> {
  const res = await apiRequest<{ data: { projects: Project[] } }>("/api/projects");
  return (res as any).data?.projects || (res as any).projects || [];
}

export async function uploadRepo(
  projectName: string,
  repoUrl?: string,
  file?: File,
): Promise<Project> {
  const formData = new FormData();
  formData.append("project_name", projectName);

  if (file) {
    formData.append("file", file);
  } else if (repoUrl) {
    formData.append("repo_url", repoUrl);
  }

  const url = `${API_BASE}/api/upload-repo`;
  const response = await fetch(url, { method: "POST", body: formData });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Upload failed: ${response.status}`);
  }

  const result = await response.json();
  return result.data || result;
}

export async function startScan(projectId: string, force: boolean = false): Promise<any> {
  return apiRequest("/api/start-scan", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId, force }),
  });
}

export async function getScanStatus(projectId: string): Promise<ScanStatus> {
  const res = await apiRequest<any>(`/api/scan-status/${projectId}`);
  return res.data || res;
}

export async function getSecurityIntelligence(projectId: string): Promise<SecurityIntelligence> {
  const res = await apiRequest<any>(`/api/security-intelligence/${projectId}`);
  return res.data || res;
}

export async function getSecurityReport(projectId: string): Promise<any> {
  const res = await apiRequest<any>(`/api/report/${projectId}`);
  return res.data || res;
}

export function getScanStreamUrl(projectId: string): string {
  return `${API_BASE}/api/scan-stream/${projectId}`;
}

export async function getCandidateRepoScan(
  candidateId: string,
  projectId: string,
  resumeText: string,
): Promise<{ security_intelligence: SecurityIntelligence; skill_inflation: SkillInflation | null }> {
  const res = await apiRequest<any>("/api/candidate-repo-scan", {
    method: "POST",
    body: JSON.stringify({ candidate_id: candidateId, project_id: projectId, resume_text: resumeText }),
  });
  return res.data || res;
}

// ──────────────────── URL / Website Security Scan ────────────────────

export interface UrlScanStartResponse {
  scan_id: string;
  target_url: string;
  status: string;
  message: string;
  disclaimer?: string;
}

export interface UrlScanVulnerability {
  id?: string;
  title: string;
  severity: string;
  endpoint: string;
  parameter: string;
  description: string;
  payload: string;
  evidence: string;
  impact: string;
  exploit_steps: string[];
  patch_recommendation: string;
  risk_score: number;
  confidence: number;
  why_missed: string;
}

export interface UrlScanResults {
  scan_id: string;
  target_url: string;
  security_posture_score: number;
  vulnerabilities: UrlScanVulnerability[];
  attack_paths: Array<{ title: string; nodes: Array<{ id: string; label: string; type: string }>; edges: Array<{ source: string; target: string }> }>;
  summary: Record<string, unknown>;
  agent_logs: Array<{ agent_name: string; message: string; log_type?: string }>;
  discovered_endpoints?: { pages: unknown[]; forms: unknown[]; api_endpoints: unknown[] };
  status: string;
}

export async function startUrlScan(url: string): Promise<UrlScanStartResponse> {
  const res = await apiRequestWithErrorHandling<any>("/api/scan/url", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
  return res.data ?? res;
}

export async function startUrlScanWithAuth(
  url: string,
  credentials: { username: string; password: string }
): Promise<UrlScanStartResponse> {
  const res = await apiRequest<any>("/api/scan/url-with-auth", {
    method: "POST",
    body: JSON.stringify({ url, credentials }),
  });
  return res.data ?? res;
}

export async function getUrlScanStatus(scanId: string): Promise<{ scan_id: string; status: string; target_url: string; security_posture_score: number }> {
  const res = await apiRequest<any>(`/api/url-scan-status/${scanId}`);
  return res.data ?? res;
}

export async function getUrlScanResults(scanId: string): Promise<UrlScanResults> {
  const res = await apiRequest<any>(`/api/url-results/${scanId}`);
  return res.data ?? res;
}
