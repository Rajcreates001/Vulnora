/**
 * Zustand store for global application state.
 */

import { create } from "zustand";
import type {
  Candidate,
  CandidateDetail,
  Evaluation,
  AgentLog,
} from "@/lib/api";

interface AppState {
  // Candidates
  candidates: Candidate[];
  selectedCandidate: CandidateDetail | null;
  setCandidates: (candidates: Candidate[]) => void;
  setSelectedCandidate: (candidate: CandidateDetail | null) => void;
  addCandidate: (candidate: Candidate) => void;
  removeCandidate: (id: string) => void;
  updateCandidateStatus: (id: string, status: string) => void;

  // Evaluation
  currentEvaluation: Evaluation | null;
  setCurrentEvaluation: (evaluation: Evaluation | null) => void;
  isEvaluating: boolean;
  setIsEvaluating: (loading: boolean) => void;

  // Agent Logs
  agentLogs: AgentLog[];
  setAgentLogs: (logs: AgentLog[]) => void;

  // UI State
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Candidates
  candidates: [],
  selectedCandidate: null,
  setCandidates: (candidates) => set({ candidates }),
  setSelectedCandidate: (candidate) =>
    set({ selectedCandidate: candidate }),
  addCandidate: (candidate) =>
    set((state) => ({
      candidates: [candidate, ...state.candidates],
    })),
  removeCandidate: (id) =>
    set((state) => ({
      candidates: state.candidates.filter((c) => c.id !== id),
    })),
  updateCandidateStatus: (id, status) =>
    set((state) => ({
      candidates: state.candidates.map((c) =>
        c.id === id ? { ...c, status } : c
      ),
    })),

  // Evaluation
  currentEvaluation: null,
  setCurrentEvaluation: (evaluation) => set({ currentEvaluation: evaluation }),
  isEvaluating: false,
  setIsEvaluating: (loading) => set({ isEvaluating: loading }),

  // Agent Logs
  agentLogs: [],
  setAgentLogs: (logs) => set({ agentLogs: logs }),

  // UI State
  activeTab: "overview",
  setActiveTab: (tab) => set({ activeTab: tab }),
}));
