const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API Error: ${res.status}`);
  }

  const json = await res.json();
  // Backend wraps all responses in { success, message, data }
  // Unwrap the data field for callers
  if (json && typeof json === "object" && "success" in json && "data" in json) {
    return json.data as T;
  }
  return json as T;
}

// ─── Projects ─────────────────────────────────────

export async function uploadRepo(formData: FormData) {
  const res = await fetch(`${API_BASE}/api/upload-repo`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail);
  }
  const json = await res.json();
  if (json && typeof json === "object" && "success" in json && "data" in json) {
    return json.data;
  }
  return json;
}

export async function getProjects() {
  return fetchAPI<{ projects: any[]; total: number }>("/api/projects");
}

export async function getProject(id: string) {
  return fetchAPI<any>(`/api/projects/${id}`);
}

export async function deleteProject(id: string) {
  return fetchAPI<{ success: boolean; message: string }>(`/api/projects/${id}`, {
    method: "DELETE",
  });
}

// ─── Scanning ─────────────────────────────────────

export async function startScan(projectId: string, force: boolean = false) {
  return fetchAPI<{
    success: boolean;
    project_id: string;
    status: string;
    current_agent: string;
    progress: number;
    agents_completed: string[];
    message: string;
  }>("/api/start-scan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: projectId, force }),
  });
}

export async function getScanStatus(projectId: string) {
  return fetchAPI<{
    project_id: string;
    status: string;
    current_agent: string;
    progress: number;
    agents_completed: string[];
    message: string;
  }>(`/api/scan-status/${projectId}`);
}

// ─── Results ──────────────────────────────────────

export async function getResults(projectId: string) {
  return fetchAPI<{
    project_id: string;
    vulnerabilities: any[];
    total: number;
    critical_count: number;
    high_count: number;
    medium_count: number;
    low_count: number;
    report: any;
    attack_paths: any[];
  }>(`/api/results/${projectId}`);
}

export async function getVulnerability(id: string) {
  return fetchAPI<any>(`/api/vulnerabilities/${id}`);
}

export async function getAgentLogs(projectId: string) {
  return fetchAPI<{ logs: any[]; total: number }>(`/api/agent-logs/${projectId}`);
}

export async function getFileContent(fileId: string) {
  return fetchAPI<any>(`/api/files/${fileId}`);
}

export async function getProjectFiles(projectId: string) {
  const project = await getProject(projectId);
  return project.files || [];
}
