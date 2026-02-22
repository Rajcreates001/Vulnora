"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import {
  Brain,
  Upload,
  Users,
  CheckCircle2,
  Clock,
  AlertCircle,
  Trash2,
  Play,
  ArrowRight,
  ArrowLeft,
  Loader2,
  Plus,
  X,
  FileText,
  Mic,
  Eye,
  Briefcase,
  RefreshCcw,
  Shield,
  Code2,
  GitBranch,
  FolderUp,
  BarChart3,
  Zap,
  Globe,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import { useAppStore } from "@/store/useAppStore";
import {
  listCandidates,
  uploadCandidate,
  uploadCandidateWithFile,
  deleteCandidate,
  resetCandidateStatus,
  extractResumeData,
  listProjects,
  uploadRepo,
  startScan,
  getScanStatus,
  startUrlScan,
  deleteProject,
} from "@/lib/api";
import type { Candidate, ResumeData, Project } from "@/lib/api";

/* ── Status / Decision Badges ── */
function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { icon: typeof Clock; label: string; className: string }> = {
    pending: { icon: Clock, label: "Pending", className: "bg-slate-500/15 text-slate-400 border-slate-500/30" },
    interviewing: { icon: Mic, label: "Interviewing", className: "bg-purple-500/15 text-purple-400 border-purple-500/30" },
    evaluating: { icon: Loader2, label: "Evaluating", className: "bg-cyan-500/15 text-cyan-400 border-cyan-500/30" },
    completed: { icon: CheckCircle2, label: "Completed", className: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30" },
    failed: { icon: AlertCircle, label: "Failed", className: "bg-red-500/15 text-red-400 border-red-500/30" },
  };
  const { icon: Icon, label, className } = config[status] || config.pending;
  return (
    <Badge className={className}>
      <Icon className={`w-3 h-3 mr-1 ${status === "evaluating" ? "animate-spin" : ""}`} />
      {label}
    </Badge>
  );
}

function ScanStatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; className: string }> = {
    pending: { label: "Pending", className: "bg-slate-500/15 text-slate-400 border-slate-500/30" },
    recon: { label: "Scanning", className: "bg-cyan-500/15 text-cyan-400 border-cyan-500/30" },
    analysis: { label: "Analyzing", className: "bg-blue-500/15 text-blue-400 border-blue-500/30" },
    exploit: { label: "Exploiting", className: "bg-amber-500/15 text-amber-400 border-amber-500/30" },
    patch: { label: "Patching", className: "bg-purple-500/15 text-purple-400 border-purple-500/30" },
    report: { label: "Reporting", className: "bg-indigo-500/15 text-indigo-400 border-indigo-500/30" },
    completed: { label: "Complete", className: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30" },
    failed: { label: "Failed", className: "bg-red-500/15 text-red-400 border-red-500/30" },
  };
  const { label, className } = config[status] || config.pending;
  return <Badge className={className}>{label}</Badge>;
}

function DecisionBadge({ decision }: { decision?: string }) {
  if (!decision) return null;
  const d = decision.toLowerCase();
  if (d.includes("strong hire")) return <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">Strong Hire</Badge>;
  if (d.includes("hire") && !d.includes("not")) return <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">Hire</Badge>;
  if (d.includes("hold") || d.includes("conditional")) return <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30">Hold</Badge>;
  if (d.includes("reject") || d.includes("not")) return <Badge className="bg-red-500/20 text-red-400 border-red-500/30">Reject</Badge>;
  return <Badge variant="secondary">{decision}</Badge>;
}

type WizardStep = 1 | 2 | 3 | 4;
type DashboardTab = "security" | "hiring";

export default function DashboardPage() {
  const {
    candidates,
    setCandidates,
    addCandidate,
    removeCandidate,
    updateCandidateStatus,
  } = useAppStore();

  const router = useRouter();
  const [activeTab, setActiveTab] = useState<DashboardTab>("security");
  const [showUpload, setShowUpload] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [wizardStep, setWizardStep] = useState<WizardStep>(1);

  // Hiring form state
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [resumeText, setResumeText] = useState("");
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [extractedResume, setExtractedResume] = useState<ResumeData | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [uploadMode, setUploadMode] = useState<"file" | "text">("file");
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Security state
  const [projects, setProjects] = useState<Project[]>([]);
  const [showRepoUpload, setShowRepoUpload] = useState(false);
  const [repoUrl, setRepoUrl] = useState("");
  const [projectName, setProjectName] = useState("");
  const [repoFile, setRepoFile] = useState<File | null>(null);
  const [repoUploading, setRepoUploading] = useState(false);
  const [repoUploadMode, setRepoUploadMode] = useState<"url" | "file">("url");
  const [repoError, setRepoError] = useState<string | null>(null);

  // Website URL scan
  const [webScanUrl, setWebScanUrl] = useState("");
  const [webScanStarting, setWebScanStarting] = useState(false);
  const [webScanError, setWebScanError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const repoFileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadCandidates();
    loadProjects();
  }, []);

  async function loadCandidates() {
    try {
      const data = await listCandidates();
      setCandidates(data);
    } catch { }
  }

  async function loadProjects() {
    try {
      const data = await listProjects();
      setProjects(data);
    } catch { }
  }

  function resetForm() {
    setName("");
    setEmail("");
    setJobDescription("");
    setResumeText("");
    setResumeFile(null);
    setExtractedResume(null);
    setExtracting(false);
    setUploadMode("file");
    setUploadError(null);
    setWizardStep(1);
  }

  function closeModal() {
    setShowUpload(false);
    resetForm();
  }

  async function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (!["pdf", "docx", "txt"].includes(ext || "")) {
      setUploadError("Only PDF, DOCX, or TXT files are supported.");
      return;
    }
    setResumeFile(file);
    setUploadError(null);
  }

  async function handleUpload() {
    if (!name || !jobDescription) return;
    setUploading(true);
    setUploadError(null);
    try {
      let candidate: Candidate;
      if (uploadMode === "file" && resumeFile) {
        const formData = new FormData();
        formData.append("name", name);
        if (email) formData.append("email", email);
        formData.append("job_description", jobDescription);
        formData.append("resume", resumeFile);
        candidate = await uploadCandidateWithFile(formData);
      } else {
        candidate = await uploadCandidate({
          name,
          email: email || undefined,
          resume_text: resumeText,
          job_description: jobDescription,
        });
      }
      addCandidate(candidate);
      closeModal();
    } catch (err: any) {
      setUploadError(err.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  function handleRunEvaluation(candidateId: string) {
    updateCandidateStatus(candidateId, "evaluating");
    router.push(`/evaluation/${candidateId}?live=true`);
  }

  function handleStartInterview(candidateId: string) {
    router.push(`/interview/${candidateId}`);
  }

  async function handleDelete(candidateId: string) {
    try {
      await deleteCandidate(candidateId);
      removeCandidate(candidateId);
    } catch { }
  }

  async function handleResetCandidate(candidateId: string) {
    try {
      await resetCandidateStatus(candidateId);
      updateCandidateStatus(candidateId, "pending");
    } catch { }
  }

  const canProceed = () => {
    switch (wizardStep) {
      case 1: return name.trim().length > 0;
      case 2: return jobDescription.trim().length > 10;
      case 3: return (uploadMode === "file" && resumeFile !== null) || (uploadMode === "text" && resumeText.trim().length > 10);
      case 4: return true;
      default: return false;
    }
  };

  // Security: upload repo
  async function handleRepoUpload() {
    if (!projectName.trim()) return;
    setRepoUploading(true);
    setRepoError(null);
    try {
      const result = await uploadRepo(
        projectName,
        repoUploadMode === "url" ? repoUrl : undefined,
        repoUploadMode === "file" ? repoFile || undefined : undefined,
      );
      setProjects((prev) => [result, ...prev]);
      setShowRepoUpload(false);
      setProjectName("");
      setRepoUrl("");
      setRepoFile(null);
    } catch (err: any) {
      setRepoError(err.message || "Upload failed");
    } finally {
      setRepoUploading(false);
    }
  }

  async function handleStartScan(projectId: string) {
    try {
      await startScan(projectId);
      setProjects((prev) =>
        prev.map((p) => (p.id === projectId ? { ...p, scan_status: "recon" } : p))
      );
      router.push(`/results/${projectId}`);
    } catch (err: any) {
      console.error(err);
    }
  }

  async function handleDeleteProject(projectId: string) {
    try {
      await deleteProject(projectId);
      setProjects((prev) => prev.filter((p) => p.id !== projectId));
    } catch (err) {
      console.error(err);
    }
  }

  const hiringStats = {
    total: candidates.length,
    completed: candidates.filter((c) => c.status === "completed").length,
    pending: candidates.filter((c) => c.status === "pending").length,
    evaluating: candidates.filter((c) => c.status === "evaluating").length,
  };

  const securityStats = {
    total: projects.length,
    completed: projects.filter((p) => p.scan_status === "completed").length,
    scanning: projects.filter((p) => !["pending", "completed", "failed"].includes(p.scan_status || "pending")).length,
  };

  const stepLabels = ["Candidate Info", "Job Description", "Resume", "Review & Submit"];

  return (
    <div className="min-h-screen bg-background">
      {/* ─── Top Bar ─── */}
      <header className="sticky top-0 z-50 bg-background/60 backdrop-blur-2xl border-b border-white/[0.04]">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[hsl(170,80%,50%)] to-[hsl(260,60%,55%)] flex items-center justify-center shadow-lg shadow-[hsl(170,80%,50%)]/20">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold tracking-tight">VERDEXA</span>
            <span className="text-xs text-muted-foreground">Dashboard</span>
          </Link>
          <div className="flex items-center gap-2">
            {activeTab === "hiring" ? (
              <Button onClick={() => setShowUpload(true)} size="sm" className="bg-gradient-to-r from-[hsl(260,60%,55%)] to-[hsl(280,70%,50%)] text-white hover:opacity-90">
                <Plus className="w-4 h-4 mr-1" />
                New Candidate
              </Button>
            ) : (
              <Button onClick={() => setShowRepoUpload(true)} size="sm" className="bg-gradient-to-r from-[hsl(170,80%,50%)] to-[hsl(200,70%,50%)] text-background hover:opacity-90">
                <Plus className="w-4 h-4 mr-1" />
                New Scan
              </Button>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* ─── Tab Navigation ─── */}
        <div className="flex gap-1 mb-8 glass-card p-1 w-fit">
          <button
            onClick={() => setActiveTab("security")}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 ${activeTab === "security"
                ? "bg-[hsl(170,80%,50%)]/15 text-[hsl(170,80%,60%)] shadow-lg shadow-[hsl(170,80%,50%)]/5"
                : "text-muted-foreground hover:text-foreground"
              }`}
          >
            <Shield className="w-4 h-4" />
            Code Security
          </button>
          <button
            onClick={() => setActiveTab("hiring")}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 ${activeTab === "hiring"
                ? "bg-[hsl(260,60%,55%)]/15 text-[hsl(260,60%,65%)] shadow-lg shadow-[hsl(260,60%,55%)]/5"
                : "text-muted-foreground hover:text-foreground"
              }`}
          >
            <Brain className="w-4 h-4" />
            Security Hiring
          </button>
        </div>

        <AnimatePresence mode="wait">
          {/* ════════════════ CODE SECURITY TAB ════════════════ */}
          {activeTab === "security" && (
            <motion.div
              key="security"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
            >
              {/* Website Security Scan */}
              <Card className="glass-card mb-8 border-[hsl(200,70%,50%)]/20">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Globe className="w-5 h-5 text-[hsl(200,70%,50%)]" />
                    Website Security Scan
                  </CardTitle>
                  <p className="text-xs text-muted-foreground">
                    Enter a URL to crawl and test for SQLi, XSS, path traversal, open redirect, and more. Only scan systems you own or have permission to test.
                  </p>
                </CardHeader>
                <CardContent className="flex flex-col sm:flex-row gap-3">
                  <Input
                    placeholder="https://example.com"
                    value={webScanUrl}
                    onChange={(e) => { setWebScanUrl(e.target.value); setWebScanError(null); }}
                    className="flex-1 bg-background/50 border-white/10"
                  />
                  <Button
                    disabled={!webScanUrl.trim() || webScanStarting}
                    onClick={async () => {
                      setWebScanStarting(true);
                      setWebScanError(null);
                      try {
                        const res = await startUrlScan(webScanUrl.trim());
                        router.push(`/webscan/${res.scan_id}`);
                      } catch (err: any) {
                        setWebScanError(err?.message || "Failed to start scan");
                      } finally {
                        setWebScanStarting(false);
                      }
                    }}
                    className="bg-gradient-to-r from-[hsl(200,70%,50%)] to-cyan-500 text-white hover:opacity-90 shrink-0"
                  >
                    {webScanStarting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                    {webScanStarting ? "Starting…" : "Scan URL"}
                  </Button>
                </CardContent>
                {webScanError && (
                  <div className="px-6 pb-4 text-sm text-red-400">{webScanError}</div>
                )}
              </Card>

              {/* Security Stats */}
              <div className="grid grid-cols-3 gap-4 mb-8">
                {[
                  { label: "Total Projects", value: securityStats.total, icon: Code2, color: "text-[hsl(170,80%,60%)]" },
                  { label: "Scans Completed", value: securityStats.completed, icon: CheckCircle2, color: "text-emerald-400" },
                  { label: "Scanning", value: securityStats.scanning, icon: Loader2, color: "text-cyan-400" },
                ].map((stat, i) => (
                  <motion.div
                    key={stat.label}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.08 }}
                  >
                    <Card className="glass-card hover:scale-[1.02] transition-transform duration-300">
                      <CardContent className="p-5">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-xs text-muted-foreground mb-1">{stat.label}</p>
                            <p className="text-2xl font-bold">{stat.value}</p>
                          </div>
                          <stat.icon className={`w-8 h-8 ${stat.color} opacity-40`} />
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </div>

              {/* Projects List */}
              <div className="space-y-3">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-bold">Projects</h2>
                </div>

                {projects.length === 0 ? (
                  <Card className="glass-card">
                    <CardContent className="py-16 text-center">
                      <Code2 className="w-12 h-12 text-muted-foreground mx-auto mb-4 opacity-50" />
                      <p className="text-muted-foreground mb-4">No projects uploaded yet.</p>
                      <Button onClick={() => setShowRepoUpload(true)} className="bg-gradient-to-r from-[hsl(170,80%,50%)] to-[hsl(200,70%,50%)] text-background">
                        <Plus className="w-4 h-4 mr-1" />
                        Upload First Project
                      </Button>
                    </CardContent>
                  </Card>
                ) : (
                  projects.map((project, i) => (
                    <motion.div
                      key={project.id}
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.06 }}
                      whileHover={{ scale: 1.005, y: -1 }}
                    >
                      <Card className="glass-card-hover">
                        <CardContent className="p-5">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                              <div className="w-10 h-10 rounded-xl bg-[hsl(170,80%,50%)]/10 flex items-center justify-center">
                                <Code2 className="w-5 h-5 text-[hsl(170,80%,60%)]" />
                              </div>
                              <div>
                                <p className="font-semibold">{project.name}</p>
                                <p className="text-xs text-muted-foreground">
                                  {project.repo_path ? "GitHub" : "ZIP Upload"} &middot;{" "}
                                  {new Date(project.created_at).toLocaleDateString()}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <ScanStatusBadge status={project.scan_status || "pending"} />

                              {(project.scan_status === "pending" ||
                                project.scan_status === "failed" ||
                                project.scan_status === "completed") && (
                                <Button
                                  size="sm"
                                  onClick={() => handleStartScan(project.id)}
                                  className="bg-gradient-to-r from-[hsl(170,80%,50%)] to-[hsl(200,70%,50%)] text-background"
                                >
                                  <Zap className="w-3.5 h-3.5 mr-1" />
                                  {project.scan_status === "completed" ? "Re-Scan" : "Scan"}
                                </Button>
                              )}

                              {project.scan_status === "completed" && (
                                <Link href={`/results/${project.id}`}>
                                  <Button size="sm" variant="outline">
                                    <Eye className="w-3.5 h-3.5 mr-1" />
                                    Results
                                  </Button>
                                </Link>
                              )}

                              {!["pending", "completed", "failed"].includes(project.scan_status || "pending") && (
                                <Link href={`/results/${project.id}`}>
                                  <Button size="sm" variant="outline">
                                    <BarChart3 className="w-3.5 h-3.5 mr-1" />
                                    Progress
                                  </Button>
                                </Link>
                              )}

                              <Button
                                size="icon"
                                variant="outline"
                                className="border-red-500/40 text-red-400 hover:bg-red-500/10"
                                onClick={() => handleDeleteProject(project.id)}
                                aria-label="Delete project"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  ))
                )}
              </div>
            </motion.div>
          )}

          {/* ════════════════ SECURITY HIRING TAB ════════════════ */}
          {activeTab === "hiring" && (
            <motion.div
              key="hiring"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
            >
              {/* Hiring Stats */}
              <div className="grid grid-cols-4 gap-4 mb-8">
                {[
                  { label: "Total Candidates", value: hiringStats.total, icon: Users, color: "text-[hsl(260,60%,65%)]" },
                  { label: "Completed", value: hiringStats.completed, icon: CheckCircle2, color: "text-emerald-400" },
                  { label: "Pending", value: hiringStats.pending, icon: Clock, color: "text-amber-400" },
                  { label: "In Progress", value: hiringStats.evaluating, icon: Loader2, color: "text-cyan-400" },
                ].map((stat, i) => (
                  <motion.div
                    key={stat.label}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.08 }}
                  >
                    <Card className="glass-card hover:scale-[1.02] transition-transform duration-300">
                      <CardContent className="p-5">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-xs text-muted-foreground mb-1">{stat.label}</p>
                            <p className="text-2xl font-bold">{stat.value}</p>
                          </div>
                          <stat.icon className={`w-8 h-8 ${stat.color} opacity-40`} />
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </div>

              {/* Candidate List */}
              <div className="space-y-3">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-bold">Candidates</h2>
                </div>

                {candidates.length === 0 ? (
                  <Card className="glass-card">
                    <CardContent className="py-16 text-center">
                      <Users className="w-12 h-12 text-muted-foreground mx-auto mb-4 opacity-50" />
                      <p className="text-muted-foreground mb-4">No candidates uploaded yet.</p>
                      <Button onClick={() => setShowUpload(true)} className="bg-gradient-to-r from-[hsl(260,60%,55%)] to-[hsl(280,70%,50%)] text-white">
                        <Plus className="w-4 h-4 mr-1" />
                        Upload First Candidate
                      </Button>
                    </CardContent>
                  </Card>
                ) : (
                  candidates.map((candidate, i) => (
                    <motion.div
                      key={candidate.id}
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.06 }}
                      whileHover={{ scale: 1.005, y: -1 }}
                    >
                      <Card className="glass-card-hover">
                        <CardContent className="p-5">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                              <div className="w-10 h-10 rounded-xl bg-[hsl(260,60%,55%)]/10 flex items-center justify-center">
                                <Users className="w-5 h-5 text-[hsl(260,60%,65%)]" />
                              </div>
                              <div>
                                <p className="font-semibold">{candidate.name}</p>
                                <p className="text-xs text-muted-foreground">
                                  {candidate.email || "No email"} &middot;{" "}
                                  {new Date(candidate.created_at).toLocaleDateString()}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <StatusBadge status={candidate.status} />

                              {(candidate.status === "pending" || candidate.status === "interviewing") && (
                                <>
                                  <Button size="sm" variant="outline" onClick={() => handleStartInterview(candidate.id)}>
                                    <Mic className="w-3.5 h-3.5 mr-1" />
                                    Interview
                                  </Button>
                                  <Button size="sm" onClick={() => handleRunEvaluation(candidate.id)} className="bg-gradient-to-r from-[hsl(260,60%,55%)] to-[hsl(280,70%,50%)] text-white">
                                    <Play className="w-3.5 h-3.5 mr-1" />
                                    Evaluate
                                  </Button>
                                </>
                              )}

                              {candidate.status === "completed" && (
                                <>
                                  <Link href={`/evaluation/${candidate.id}`}>
                                    <Button size="sm" variant="outline">
                                      <Eye className="w-3.5 h-3.5 mr-1" />
                                      View Results
                                    </Button>
                                  </Link>
                                  <Button size="sm" variant="ghost" onClick={() => handleResetCandidate(candidate.id)} title="Re-evaluate">
                                    <RefreshCcw className="w-3.5 h-3.5" />
                                  </Button>
                                </>
                              )}

                              {candidate.status === "failed" && (
                                <Button size="sm" variant="ghost" onClick={() => handleResetCandidate(candidate.id)}>
                                  <RefreshCcw className="w-3.5 h-3.5 mr-1" />
                                  Retry
                                </Button>
                              )}

                              <Button size="icon" variant="ghost" className="text-muted-foreground hover:text-destructive" onClick={() => handleDelete(candidate.id)}>
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  ))
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ─── Upload Candidate Modal (Hiring) ─── */}
        <AnimatePresence>
          {showUpload && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
              onClick={(e) => e.target === e.currentTarget && closeModal()}
            >
              <motion.div
                initial={{ scale: 0.92, opacity: 0, y: 10 }}
                animate={{ scale: 1, opacity: 1, y: 0 }}
                exit={{ scale: 0.92, opacity: 0, y: 10 }}
                transition={{ type: "spring", stiffness: 300, damping: 25 }}
                className="w-full max-w-2xl max-h-[90vh] overflow-y-auto"
              >
                <Card className="glass-card glow-border">
                  <CardHeader className="flex flex-row items-center justify-between pb-3">
                    <CardTitle className="flex items-center gap-2">
                      <Upload className="w-5 h-5 text-[hsl(260,60%,65%)]" />
                      Add New Candidate
                    </CardTitle>
                    <Button variant="ghost" size="icon" onClick={closeModal}>
                      <X className="w-4 h-4" />
                    </Button>
                  </CardHeader>

                  {/* Step Progress */}
                  <div className="px-6 pb-4">
                    <div className="flex items-center gap-2 mb-2">
                      {stepLabels.map((label, i) => (
                        <div key={i} className="flex items-center gap-2 flex-1">
                          <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${i + 1 < wizardStep ? "bg-emerald-500 text-white"
                              : i + 1 === wizardStep ? "bg-[hsl(260,60%,55%)] text-white"
                                : "bg-muted text-muted-foreground"
                            }`}>
                            {i + 1 < wizardStep ? <CheckCircle2 className="w-3.5 h-3.5" /> : i + 1}
                          </div>
                          <span className={`text-xs hidden sm:block ${i + 1 === wizardStep ? "text-foreground font-medium" : "text-muted-foreground"
                            }`}>{label}</span>
                          {i < 3 && <div className={`flex-1 h-0.5 ${i + 1 < wizardStep ? "bg-emerald-500" : "bg-muted"}`} />}
                        </div>
                      ))}
                    </div>
                  </div>

                  <CardContent className="space-y-4">
                    {wizardStep === 1 && (
                      <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="space-y-4">
                        <div>
                          <label className="text-sm text-muted-foreground mb-1 block">Full Name *</label>
                          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g., Rohan Sharma" autoFocus />
                        </div>
                        <div>
                          <label className="text-sm text-muted-foreground mb-1 block">Email (optional)</label>
                          <Input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="candidate@email.com" type="email" />
                        </div>
                      </motion.div>
                    )}
                    {wizardStep === 2 && (
                      <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="space-y-4">
                        <div>
                          <label className="text-sm text-muted-foreground mb-1 block">
                            <Briefcase className="w-3.5 h-3.5 inline mr-1" /> Job Description *
                          </label>
                          <Textarea value={jobDescription} onChange={(e) => setJobDescription(e.target.value)} placeholder="Paste the full job description..." rows={10} autoFocus />
                          <p className="text-xs text-muted-foreground mt-1">{jobDescription.length} characters</p>
                        </div>
                      </motion.div>
                    )}
                    {wizardStep === 3 && (
                      <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="space-y-4">
                        <div className="flex gap-2">
                          <Button variant={uploadMode === "file" ? "default" : "outline"} size="sm" onClick={() => setUploadMode("file")}>
                            <Upload className="w-3.5 h-3.5 mr-1" /> Upload File
                          </Button>
                          <Button variant={uploadMode === "text" ? "default" : "outline"} size="sm" onClick={() => setUploadMode("text")}>
                            <FileText className="w-3.5 h-3.5 mr-1" /> Paste Text
                          </Button>
                        </div>
                        {uploadMode === "file" ? (
                          <div>
                            <input ref={fileInputRef} type="file" accept=".pdf,.docx,.txt" onChange={handleFileSelect} className="hidden" />
                            <div onClick={() => fileInputRef.current?.click()} className="border-2 border-dashed border-white/10 rounded-xl p-8 text-center cursor-pointer hover:border-[hsl(260,60%,55%)]/30 transition-colors">
                              {resumeFile ? (
                                <div className="flex items-center justify-center gap-3">
                                  <FileText className="w-10 h-10 text-[hsl(260,60%,65%)]" />
                                  <div className="text-left">
                                    <p className="font-medium text-sm">{resumeFile.name}</p>
                                    <p className="text-xs text-muted-foreground">{(resumeFile.size / 1024).toFixed(1)} KB &middot; Click to change</p>
                                  </div>
                                </div>
                              ) : (
                                <div>
                                  <Upload className="w-10 h-10 text-muted-foreground mx-auto mb-2" />
                                  <p className="text-sm font-medium">Click to upload resume</p>
                                  <p className="text-xs text-muted-foreground mt-1">PDF, DOCX, or TXT (max 10MB)</p>
                                </div>
                              )}
                            </div>
                          </div>
                        ) : (
                          <div>
                            <label className="text-sm text-muted-foreground mb-1 block">Resume Text *</label>
                            <Textarea value={resumeText} onChange={(e) => setResumeText(e.target.value)} placeholder="Paste the candidate's resume content here..." rows={10} autoFocus />
                            <p className="text-xs text-muted-foreground mt-1">{resumeText.length} characters</p>
                          </div>
                        )}
                      </motion.div>
                    )}
                    {wizardStep === 4 && (
                      <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="space-y-4">
                        <div className="bg-muted/30 rounded-xl p-4 space-y-3">
                          <div className="flex items-center gap-2 text-sm">
                            <Users className="w-4 h-4 text-[hsl(260,60%,65%)]" />
                            <span className="text-muted-foreground">Name:</span>
                            <span className="font-medium">{name}</span>
                          </div>
                          {email && (
                            <div className="flex items-center gap-2 text-sm">
                              <span className="w-4" /><span className="text-muted-foreground">Email:</span><span className="font-medium">{email}</span>
                            </div>
                          )}
                          <Separator className="bg-white/5" />
                          <div className="text-sm">
                            <div className="flex items-center gap-2 mb-1">
                              <Briefcase className="w-4 h-4 text-[hsl(260,60%,65%)]" />
                              <span className="text-muted-foreground">Job Description</span>
                            </div>
                            <p className="text-xs text-muted-foreground ml-6 line-clamp-3">{jobDescription}</p>
                          </div>
                          <Separator className="bg-white/5" />
                          <div className="text-sm">
                            <div className="flex items-center gap-2">
                              <FileText className="w-4 h-4 text-[hsl(260,60%,65%)]" />
                              <span className="text-muted-foreground">Resume:</span>
                              <span className="font-medium">
                                {uploadMode === "file" ? resumeFile?.name : `${resumeText.length} characters`}
                              </span>
                            </div>
                          </div>
                        </div>
                        {uploadError && (
                          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 flex items-center gap-2">
                            <AlertCircle className="w-4 h-4 text-red-400" />
                            <span className="text-xs text-red-400">{uploadError}</span>
                          </div>
                        )}
                      </motion.div>
                    )}

                    <Separator className="bg-white/5" />

                    <div className="flex justify-between">
                      <Button variant="outline" onClick={() => wizardStep === 1 ? closeModal() : setWizardStep((wizardStep - 1) as WizardStep)} className="border-white/10">
                        <ArrowLeft className="w-3.5 h-3.5 mr-1" />
                        {wizardStep === 1 ? "Cancel" : "Back"}
                      </Button>
                      {wizardStep < 4 ? (
                        <Button onClick={() => setWizardStep((wizardStep + 1) as WizardStep)} disabled={!canProceed()} className="bg-gradient-to-r from-[hsl(260,60%,55%)] to-[hsl(280,70%,50%)] text-white">
                          Next <ArrowRight className="w-3.5 h-3.5 ml-1" />
                        </Button>
                      ) : (
                        <Button onClick={handleUpload} disabled={uploading} className="bg-gradient-to-r from-[hsl(260,60%,55%)] to-[hsl(280,70%,50%)] text-white">
                          {uploading ? (<><Loader2 className="w-4 h-4 mr-1 animate-spin" /> Uploading...</>) : (<><Upload className="w-4 h-4 mr-1" /> Upload Candidate</>)}
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ─── Upload Repo Modal (Security) ─── */}
        <AnimatePresence>
          {showRepoUpload && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
              onClick={(e) => e.target === e.currentTarget && setShowRepoUpload(false)}
            >
              <motion.div
                initial={{ scale: 0.92, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.92, opacity: 0 }}
                transition={{ type: "spring", stiffness: 300, damping: 25 }}
                className="w-full max-w-lg"
              >
                <Card className="glass-card glow-border">
                  <CardHeader className="flex flex-row items-center justify-between pb-3">
                    <CardTitle className="flex items-center gap-2">
                      <Shield className="w-5 h-5 text-[hsl(170,80%,60%)]" />
                      Upload Repository
                    </CardTitle>
                    <Button variant="ghost" size="icon" onClick={() => setShowRepoUpload(false)}>
                      <X className="w-4 h-4" />
                    </Button>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <label className="text-sm text-muted-foreground mb-1 block">Project Name *</label>
                      <Input value={projectName} onChange={(e) => setProjectName(e.target.value)} placeholder="e.g., my-web-app" autoFocus />
                    </div>

                    <div className="flex gap-2">
                      <Button variant={repoUploadMode === "url" ? "default" : "outline"} size="sm" onClick={() => setRepoUploadMode("url")}>
                        <GitBranch className="w-3.5 h-3.5 mr-1" /> GitHub URL
                      </Button>
                      <Button variant={repoUploadMode === "file" ? "default" : "outline"} size="sm" onClick={() => setRepoUploadMode("file")}>
                        <FolderUp className="w-3.5 h-3.5 mr-1" /> ZIP File
                      </Button>
                    </div>

                    {repoUploadMode === "url" ? (
                      <div>
                        <label className="text-sm text-muted-foreground mb-1 block">GitHub Repository URL</label>
                        <Input value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)} placeholder="https://github.com/user/repo" />
                      </div>
                    ) : (
                      <div>
                        <input ref={repoFileInputRef} type="file" accept=".zip" className="hidden" onChange={(e) => setRepoFile(e.target.files?.[0] || null)} />
                        <div onClick={() => repoFileInputRef.current?.click()} className="border-2 border-dashed border-white/10 rounded-xl p-6 text-center cursor-pointer hover:border-[hsl(170,80%,50%)]/30 transition-colors">
                          {repoFile ? (
                            <div className="flex items-center justify-center gap-3">
                              <FolderUp className="w-8 h-8 text-[hsl(170,80%,60%)]" />
                              <div className="text-left">
                                <p className="font-medium text-sm">{repoFile.name}</p>
                                <p className="text-xs text-muted-foreground">{(repoFile.size / 1024).toFixed(1)} KB</p>
                              </div>
                            </div>
                          ) : (
                            <div>
                              <FolderUp className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
                              <p className="text-sm font-medium">Click to upload ZIP</p>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {repoError && (
                      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 text-red-400" />
                        <span className="text-xs text-red-400">{repoError}</span>
                      </div>
                    )}

                    <div className="flex justify-end gap-2 pt-2">
                      <Button variant="outline" onClick={() => setShowRepoUpload(false)} className="border-white/10">Cancel</Button>
                      <Button
                        onClick={handleRepoUpload}
                        disabled={repoUploading || !projectName.trim()}
                        className="bg-gradient-to-r from-[hsl(170,80%,50%)] to-[hsl(200,70%,50%)] text-background"
                      >
                        {repoUploading ? (<><Loader2 className="w-4 h-4 mr-1 animate-spin" /> Uploading...</>) : (<><Shield className="w-4 h-4 mr-1" /> Upload & Prepare</>)}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
