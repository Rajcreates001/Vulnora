"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { VulnerabilityList } from "@/components/vulnerability-list";
import { VulnerabilityDetail } from "@/components/vulnerability-detail";
import { AttackPathGraph } from "@/components/attack-path-graph";
import { RiskCharts } from "@/components/risk-charts";
import { AgentLogs } from "@/components/agent-logs";
import { LiveAgentChat } from "@/components/live-agent-chat";
import { DetailedReport } from "@/components/detailed-report";
import { FileStructureTree } from "@/components/file-structure-tree";
import { useVulnoraStore } from "@/store/vulnora-store";
import {
  getResults,
  getProject,
  getAgentLogs,
  startScan,
  getScanStatus,
} from "@/lib/api";
import { ScanProgress } from "@/components/scan-progress";
import {
  Shield,
  BarChart3,
  GitBranch,
  ScrollText,
  Bug,
  Play,
  Loader2,
  MessageSquare,
  FileText,
  ArrowLeft,
  ChevronRight,
  FolderTree,
} from "lucide-react";
import Link from "next/link";

export default function ResultsPage() {
  const params = useParams();
  const projectId = params.projectId as string;

  const {
    currentProject,
    setCurrentProject,
    vulnerabilities,
    setVulnerabilities,
    currentVulnerability: selectedVulnerability,
    setCurrentVulnerability: setSelectedVulnerability,
    scanStatus,
    setScanStatus,
  } = useVulnoraStore();

  const [agentLogs, setAgentLogs] = useState<any[]>([]);
  const [report, setReport] = useState<any>(null);
  const [attackPaths, setAttackPaths] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [scanError, setScanError] = useState<string | null>(null);
  const [scanStarting, setScanStarting] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [proj, results, logs] = await Promise.all([
        getProject(projectId),
        getResults(projectId).catch(() => null),
        getAgentLogs(projectId).catch(() => []),
      ]);
      setCurrentProject(proj);
      setAgentLogs((logs as any)?.logs || logs || []);

      if (results) {
        setVulnerabilities(results.vulnerabilities || []);
        setReport(results.report || null);
        setAttackPaths(results.attack_paths || []);
      }

      // Check if scan in progress
      const activeStatuses = ["recon", "analysis", "exploit", "patch", "report", "scanning"];
      if (activeStatuses.includes(proj.scan_status)) {
        const status = await getScanStatus(projectId);
        setScanStatus(status);
        setScanning(true);
      }
    } catch (e) {
      console.error("Failed to load data", e);
    } finally {
      setLoading(false);
    }
  }, [projectId, setCurrentProject, setScanStatus, setVulnerabilities]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Poll for data during scanning
  useEffect(() => {
    if (!scanning) return;
    const interval = setInterval(async () => {
      try {
        const [results, logs] = await Promise.all([
          getResults(projectId).catch(() => null),
          getAgentLogs(projectId).catch(() => []),
        ]);
        setAgentLogs((logs as any)?.logs || logs || []);
        if (results) {
          setVulnerabilities(results.vulnerabilities || []);
          setReport(results.report || null);
          setAttackPaths(results.attack_paths || []);
        }

        const status = await getScanStatus(projectId);
        setScanStatus(status);
        if (status.status === "completed" || status.status === "failed") {
          setScanning(false);
          // Final reload
          loadData();
        }
      } catch {
        // Ignore polling errors
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [scanning, projectId, loadData, setScanStatus, setVulnerabilities]);

  async function handleStartScan(force: boolean = false) {
    setScanStarting(true);
    setScanError(null);
    try {
      const result = await startScan(projectId, force);
      // Use the startScan response as the initial scan status (avoids race condition)
      setScanStatus({
        project_id: projectId,
        status: result.status || "recon",
        current_agent: result.current_agent || "recon_agent",
        progress: result.progress || 0,
        agents_completed: result.agents_completed || [],
        message: result.message || "Scan starting...",
      });
      setScanning(true);
    } catch (e: any) {
      const errMsg = e?.message || "Failed to start scan";
      // If scan is already running, offer force restart
      if (errMsg.includes("already in progress")) {
        setScanError("A previous scan is still in progress. Click 'Force Restart Scan' to restart.");
      } else {
        setScanError(errMsg);
      }
    } finally {
      setScanStarting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] text-muted-foreground">
        <Loader2 className="h-6 w-6 animate-spin mr-2" />
        Loading…
      </div>
    );
  }

  const sevCounts = (vulnerabilities || []).reduce(
    (acc: Record<string, number>, v: any) => {
      const key = (v.severity || "info").toLowerCase();
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    },
    {}
  );

  return (
    <div className="max-w-7xl mx-auto px-6 py-10">
      {/* Breadcrumb Navigation */}
      <motion.div
        className="mb-4"
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Link href="/dashboard" className="hover:text-foreground transition-colors flex items-center gap-1">
            <ArrowLeft className="h-3.5 w-3.5" />
            Dashboard
          </Link>
          <ChevronRight className="h-3.5 w-3.5" />
          <span className="text-foreground font-medium truncate max-w-[300px]">
            {currentProject?.name || "Project"}
          </span>
        </div>
      </motion.div>

      {/* Header */}
      <motion.div
        className="mb-8"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-bold">
              {currentProject?.name || "Project"}
            </h1>
            <p className="text-muted-foreground text-sm mt-1">
              {vulnerabilities.length} vulnerabilities found
            </p>
          </div>
          <div className="flex items-center gap-2">
            {["critical", "high", "medium", "low"].map(
              (sev) =>
                sevCounts[sev] > 0 && (
                  <Badge key={sev} variant={sev as any}>
                    {sevCounts[sev]} {sev}
                  </Badge>
                )
            )}
            {scanning ? (
              <Button size="sm" className="gap-1.5 bg-blue-600/20 text-blue-400 border border-blue-500/30" disabled>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Scanning...
              </Button>
            ) : scanStarting ? (
              <Button size="sm" className="gap-1.5" disabled>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Starting...
              </Button>
            ) : (
              <>
                <Button
                  size="sm"
                  className="gap-1 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white"
                  onClick={() => handleStartScan(false)}
                >
                  <Play className="h-3.5 w-3.5" />
                  {currentProject?.scan_status === "completed" ? "Re-Scan" : "Start Scan"}
                </Button>
                {scanError && scanError.includes("already in progress") && (
                  <Button
                    size="sm"
                    variant="destructive"
                    className="gap-1"
                    onClick={() => handleStartScan(true)}
                  >
                    <Play className="h-3.5 w-3.5" />
                    Force Restart
                  </Button>
                )}
              </>
            )}
          </div>
        </div>
      </motion.div>

      {/* Scan Error Message */}
      {scanError && (
        <motion.div
          className="mb-6"
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="rounded-lg border border-red-500/30 bg-red-500/5 px-4 py-3 text-sm text-red-400 flex items-center justify-between">
            <span>{scanError}</span>
            <Button
              size="sm"
              variant="ghost"
              className="text-red-400 hover:text-red-300 h-7 px-2"
              onClick={() => setScanError(null)}
            >
              Dismiss
            </Button>
          </div>
        </motion.div>
      )}

      {/* Active Scan */}
      {scanning && (
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <ScanProgress
            projectId={projectId}
            scanStatus={scanStatus}
            onComplete={() => {
              setScanning(false);
              loadData();
            }}
          />
        </motion.div>
      )}

      {/* Executive Summary */}
      {report?.executive_summary && (
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="border-border/50 bg-card/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <Shield className="h-5 w-5 text-indigo-400" />
                Executive Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {report.executive_summary}
              </p>
              {report.overall_risk_rating && (
                <Badge variant="outline" className="mt-3 text-xs">
                  Overall Risk: {report.overall_risk_rating}
                </Badge>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Main Tabs */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Tabs defaultValue="vulnerabilities">
          <TabsList className="mb-6">
            <TabsTrigger value="vulnerabilities" className="gap-1.5">
              <Bug className="h-3.5 w-3.5" />
              Vulnerabilities
            </TabsTrigger>
            <TabsTrigger value="charts" className="gap-1.5">
              <BarChart3 className="h-3.5 w-3.5" />
              Risk Analytics
            </TabsTrigger>
            <TabsTrigger value="attack-paths" className="gap-1.5">
              <GitBranch className="h-3.5 w-3.5" />
              Attack Paths
            </TabsTrigger>
            <TabsTrigger value="logs" className="gap-1.5">
              <ScrollText className="h-3.5 w-3.5" />
              Agent Logs
            </TabsTrigger>
            <TabsTrigger value="live-chat" className="gap-1.5">
              <MessageSquare className="h-3.5 w-3.5" />
              Live Chat
            </TabsTrigger>
            <TabsTrigger value="report" className="gap-1.5">
              <FileText className="h-3.5 w-3.5" />
              Full Report
            </TabsTrigger>
            <TabsTrigger value="file-structure" className="gap-1.5">
              <FolderTree className="h-3.5 w-3.5" />
              File Structure
            </TabsTrigger>
          </TabsList>

          <TabsContent value="vulnerabilities">
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
              <div className="lg:col-span-2">
                <VulnerabilityList
                  vulnerabilities={vulnerabilities}
                  selectedId={selectedVulnerability?.id}
                  onSelect={(v) => setSelectedVulnerability(v as any)}
                />
              </div>
              <div className="lg:col-span-3">
                {selectedVulnerability ? (
                  <VulnerabilityDetail vulnerability={selectedVulnerability} />
                ) : (
                  <Card className="border-border/50 bg-card/50">
                    <CardContent className="flex items-center justify-center py-24 text-muted-foreground">
                      <p className="text-sm">
                        Select a vulnerability to view details
                      </p>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          </TabsContent>

          <TabsContent value="charts">
            <RiskCharts vulnerabilities={vulnerabilities} />
          </TabsContent>

          <TabsContent value="attack-paths">
            <AttackPathGraph attackPaths={attackPaths} />
          </TabsContent>

          <TabsContent value="logs">
            <AgentLogs logs={agentLogs} />
          </TabsContent>

          <TabsContent value="live-chat">
            <LiveAgentChat projectId={projectId} isScanning={scanning} />
          </TabsContent>

          <TabsContent value="report">
            <DetailedReport projectId={projectId} />
          </TabsContent>

          <TabsContent value="file-structure">
            <FileStructureTree projectId={projectId} vulnerabilities={vulnerabilities} />
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
}
