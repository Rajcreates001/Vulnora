import { create } from "zustand";

export interface Project {
  id: string;
  name: string;
  repo_path?: string;
  scan_status: string;
  created_at: string;
  file_count?: number;
  vulnerability_count?: number;
}

export interface Vulnerability {
  id: string;
  project_id: string;
  title: string;
  vulnerability_type: string;
  severity: "Critical" | "High" | "Medium" | "Low";
  description: string;
  file_path: string;
  line_start: number;
  line_end: number;
  vulnerable_code: string;
  exploit?: string;
  exploit_script?: string;
  patch?: string;
  patch_explanation?: string;
  risk_score: number;
  confidence: number;
  exploitability: number;
  impact: number;
  cwe_id?: string;
  cvss_vector?: string;
  attack_path?: any[];
  created_at: string;
}

export interface AgentLog {
  id: string;
  project_id: string;
  agent_name: string;
  message: string;
  log_type: string;
  data?: any;
  timestamp: string;
}

export interface ScanStatus {
  project_id: string;
  status: string;
  current_agent: string;
  progress: number;
  agents_completed: string[];
  message: string;
}

interface VulnoraStore {
  // Projects
  projects: Project[];
  currentProject: Project | null;
  setProjects: (projects: Project[]) => void;
  setCurrentProject: (project: Project | null) => void;

  // Scan
  scanStatus: ScanStatus | null;
  setScanStatus: (status: ScanStatus | null) => void;

  // Vulnerabilities
  vulnerabilities: Vulnerability[];
  currentVulnerability: Vulnerability | null;
  setVulnerabilities: (vulns: Vulnerability[]) => void;
  setCurrentVulnerability: (vuln: Vulnerability | null) => void;

  // Agent Logs
  agentLogs: AgentLog[];
  setAgentLogs: (logs: AgentLog[]) => void;

  // Report
  report: any;
  setReport: (report: any) => void;

  // UI State
  isUploading: boolean;
  isScanning: boolean;
  selectedTab: string;
  setIsUploading: (v: boolean) => void;
  setIsScanning: (v: boolean) => void;
  setSelectedTab: (tab: string) => void;
}

export const useVulnoraStore = create<VulnoraStore>((set) => ({
  projects: [],
  currentProject: null,
  setProjects: (projects) => set({ projects }),
  setCurrentProject: (project) => set({ currentProject: project }),

  scanStatus: null,
  setScanStatus: (status) => set({ scanStatus: status }),

  vulnerabilities: [],
  currentVulnerability: null,
  setVulnerabilities: (vulns) => set({ vulnerabilities: vulns }),
  setCurrentVulnerability: (vuln) => set({ currentVulnerability: vuln }),

  agentLogs: [],
  setAgentLogs: (logs) => set({ agentLogs: logs }),

  report: null,
  setReport: (report) => set({ report }),

  isUploading: false,
  isScanning: false,
  selectedTab: "vulnerabilities",
  setIsUploading: (v) => set({ isUploading: v }),
  setIsScanning: (v) => set({ isScanning: v }),
  setSelectedTab: (tab) => set({ selectedTab: tab }),
}));
