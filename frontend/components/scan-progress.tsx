"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Search, Shield, Bug, Swords, Wrench, BarChart3, MessageSquare, FileText, CheckCircle2, Loader2, AlertCircle,
} from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getScanStatus } from "@/lib/api";

const PIPELINE_STAGES = [
  { key: "recon_agent", label: "Reconnaissance", icon: Search, description: "Analyzing structure" },
  { key: "static_analysis_agent", label: "Static Analysis", icon: Shield, description: "Running tools" },
  { key: "vulnerability_discovery_agent", label: "Vulnerability Scan", icon: Bug, description: "Finding vulns" },
  { key: "exploit_simulation_agent", label: "Exploit Simulation", icon: Swords, description: "Simulating attacks" },
  { key: "patch_generation_agent", label: "Patch Generation", icon: Wrench, description: "Creating fixes" },
  { key: "risk_prioritization_agent", label: "Risk Scoring", icon: BarChart3, description: "Scoring risks" },
  { key: "alert_reduction_agent", label: "Alert Reduction", icon: AlertCircle, description: "Deduplicating and prioritizing alerts" },
  { key: "insight_agent", label: "Insight Generation", icon: FileText, description: "Human-level insights and context" },
  { key: "missed_vuln_reasoning_agent", label: "Missed Vuln Reasoning", icon: MessageSquare, description: "Why vulns were missed" },
  { key: "security_debate_agent", label: "Verification", icon: MessageSquare, description: "Debating findings" },
  { key: "report_generation_agent", label: "Report", icon: FileText, description: "Creating report" },
];

interface ScanProgressProps {
  projectId: string;
  scanStatus?: any;
  onComplete?: () => void;
}

export function ScanProgress({ projectId, scanStatus: initialStatus, onComplete }: ScanProgressProps) {
  const [status, setStatus] = useState<any>(initialStatus || null);
  const [overallProgress, setOverallProgress] = useState(0);
  const [failed, setFailed] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  // Update when parent passes new initialStatus
  useEffect(() => {
    if (initialStatus) {
      setStatus(initialStatus);
    }
  }, [initialStatus]);

  useEffect(() => {
    let active = true;
    const interval = setInterval(async () => {
      if (!active) return;
      try {
        const data = await getScanStatus(projectId);
        if (!active) return;
        setStatus(data);

        const completed = data.agents_completed?.length || 0;
        const progress = (completed / PIPELINE_STAGES.length) * 100;
        setOverallProgress(Math.max(progress, (data.progress || 0) * 100));

        if (data.status === "completed") {
          clearInterval(interval);
          setOverallProgress(100);
          onComplete?.();
        } else if (data.status === "failed") {
          clearInterval(interval);
          setFailed(true);
          setErrorMessage(data.message || "Scan failed");
          onComplete?.();
        }
      } catch {
        // Ignore polling errors
      }
    }, 2000);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [projectId, onComplete]);

  const getStageStatus = (key: string) => {
    if (!status) return "pending";
    if (status.agents_completed?.includes(key)) return "completed";
    if (status.current_agent === key) return "active";
    return "pending";
  };

  return (
    <Card className="border-blue-500/20 bg-blue-500/5">
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          {failed ? (
            <AlertCircle className="h-5 w-5 text-red-400" />
          ) : status?.status === "completed" ? (
            <CheckCircle2 className="h-5 w-5 text-green-400" />
          ) : (
            <Loader2 className="h-5 w-5 animate-spin text-blue-400" />
          )}
          {failed ? "Scan Failed" : status?.status === "completed" ? "Scan Completed" : "Security Scan In Progress"}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Error message */}
        {failed && errorMessage && (
          <div className="rounded-md border border-red-500/20 bg-red-500/5 p-3 text-sm text-red-400">
            {errorMessage}
          </div>
        )}

        {/* Overall Progress */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Overall Progress</span>
            <span className="font-mono text-blue-400">{Math.round(overallProgress)}%</span>
          </div>
          <Progress value={overallProgress} className="h-2" />
          {status?.message && (
            <p className="text-xs text-muted-foreground">{status.message}</p>
          )}
        </div>

        {/* Pipeline Stages */}
        <div className="space-y-3">
          {PIPELINE_STAGES.map((stage, index) => {
            const stageStatus = getStageStatus(stage.key);
            const Icon = stage.icon;

            return (
              <motion.div
                key={stage.key}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.08, duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] }}
                className={`flex items-center gap-4 rounded-lg border p-3 transition-all duration-300 ${stageStatus === "active"
                    ? "border-blue-500/50 bg-blue-500/5 shadow-lg shadow-blue-500/10"
                    : stageStatus === "completed"
                      ? "border-green-500/30 bg-green-500/5"
                      : "border-border/50 bg-card/30"
                  }`}
              >
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-lg transition-colors duration-300 ${stageStatus === "active"
                      ? "bg-blue-500/20 text-blue-400"
                      : stageStatus === "completed"
                        ? "bg-green-500/20 text-green-400"
                        : "bg-muted text-muted-foreground"
                    }`}
                >
                  {stageStatus === "active" ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : stageStatus === "completed" ? (
                    <CheckCircle2 className="h-5 w-5" />
                  ) : (
                    <Icon className="h-5 w-5" />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-medium ${stageStatus === "active" ? "text-blue-400" :
                      stageStatus === "completed" ? "text-green-400" :
                        "text-muted-foreground"
                    }`}>
                    {stage.label}
                  </p>
                  <p className="text-xs text-muted-foreground truncate">{stage.description}</p>
                </div>

                {stageStatus === "active" && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="h-2 w-2 rounded-full bg-blue-400 animate-pulse"
                  />
                )}
                {stageStatus === "completed" && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: "spring", stiffness: 500, damping: 15 }}
                    className="h-2 w-2 rounded-full bg-green-400"
                  />
                )}
              </motion.div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
