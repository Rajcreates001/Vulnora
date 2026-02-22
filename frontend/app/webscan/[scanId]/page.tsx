"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  ArrowLeft,
  Bug,
  GitBranch,
  ScrollText,
  FileText,
  Globe,
  Loader2,
  Download,
  Shield,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";
import { getUrlScanStatus, getUrlScanResults, type UrlScanResults, type UrlScanVulnerability } from "@/lib/api";

const STAGES = [
  { key: "pending", label: "Queued" },
  { key: "crawling", label: "Crawling" },
  { key: "scanning", label: "Scanning" },
  { key: "analyzing", label: "Analyzing" },
  { key: "completed", label: "Complete" },
  { key: "failed", label: "Failed" },
];

export default function WebScanPage() {
  const params = useParams();
  const scanId = params.scanId as string;
  const router = useRouter();
  const [status, setStatus] = useState<string>("pending");
  const [results, setResults] = useState<UrlScanResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!scanId) return;
    try {
      const [st, res] = await Promise.all([
        getUrlScanStatus(scanId),
        getUrlScanResults(scanId).catch(() => null),
      ]);
      // Prioritize status from results if available, otherwise use status endpoint
      // Results endpoint is more authoritative as it reflects the actual scan state
      const finalStatus = res?.status || st.status || "pending";
      setStatus(finalStatus);
      if (res) {
        setResults(res);
      }
    } catch (e: any) {
      setError(e?.message || "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [scanId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (status === "completed" || status === "failed") return;
    const t = setInterval(load, 3000);
    return () => clearInterval(t);
  }, [status, load]);

  const downloadReport = () => {
    if (!results) return;
    const blob = new Blob([JSON.stringify(results, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `verdexa-url-scan-${scanId}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  if (loading && !results) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center text-muted-foreground">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  const targetUrl = results?.target_url || "";
  const score = results?.security_posture_score ?? 0;
  const vulns = results?.vulnerabilities ?? [];
  const attackPaths = results?.attack_paths ?? [];
  const agentLogs = results?.agent_logs ?? [];
  const summary = results?.summary as Record<string, any> | undefined;
  const isComplete = status === "completed" || status === "failed";

  return (
    <div className="max-w-7xl mx-auto px-6 py-10">
      <motion.div
        className="mb-4"
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Link href="/dashboard" className="hover:text-foreground transition-colors flex items-center gap-1">
            <ArrowLeft className="w-3.5 h-3.5" />
            Dashboard
          </Link>
          <span className="text-foreground/60">/</span>
          <span className="text-foreground font-medium truncate max-w-[280px]">Website Scan</span>
        </div>
      </motion.div>

      <motion.div
        className="mb-8"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Globe className="w-7 h-7 text-[hsl(200,70%,50%)]" />
              Website Security Scan
            </h1>
            <p className="text-muted-foreground text-sm mt-1 truncate max-w-xl">{targetUrl || "—"}</p>
          </div>
          <div className="flex items-center gap-2">
            {!isComplete ? (
              <Badge className="bg-cyan-500/15 text-cyan-400 border-cyan-500/30">
                <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                {status}
              </Badge>
            ) : status === "completed" ? (
              <Badge className="bg-emerald-500/15 text-emerald-400 border-emerald-500/30">
                <CheckCircle2 className="w-3 h-3 mr-1" />
                Completed
              </Badge>
            ) : (
              <Badge variant="destructive">Failed</Badge>
            )}
            {isComplete && results && (
              <Button size="sm" variant="outline" onClick={downloadReport} className="gap-1">
                <Download className="w-3.5 h-3.5" />
                Download Report
              </Button>
            )}
          </div>
        </div>
      </motion.div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-500/30 bg-red-500/5 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Progress pipeline */}
      <motion.div
        className="mb-8"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card className="glass-card border-[hsl(200,70%,50%)]/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Scan progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {STAGES.map((s, i) => {
                const isCompleted = status === "completed";
                const isFailed = status === "failed";
                // Stage is active only if it's the current status AND not a final state
                const active = status === s.key && !isCompleted && !isFailed;
                // Stage is done if it's before the current stage, or if scan is completed/failed
                const done = STAGES.findIndex((x) => x.key === status) > i || isCompleted || (isFailed && s.key !== "failed");
                // For final states (completed/failed), always show checkmark, not spinner
                const isFinalState = (isCompleted && s.key === "completed") || (isFailed && s.key === "failed");
                return (
                  <div
                    key={s.key}
                    className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-xs ${
                      active
                        ? "border-cyan-500/50 bg-cyan-500/10 text-cyan-400"
                        : done || isFinalState
                          ? "border-emerald-500/30 bg-emerald-500/5 text-emerald-400"
                          : "border-white/10 text-muted-foreground"
                    }`}
                  >
                    {done || isFinalState ? (
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    ) : active ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : null}
                    {s.label}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Security posture score */}
      {isComplete && (
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <Card className="glass-card">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Shield className="w-4 h-4 text-[hsl(200,70%,50%)]" />
                Security Posture Score
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-6">
                <div className="flex-1 max-w-xs">
                  <Progress value={score} className="h-3" />
                </div>
                <span className="text-2xl font-bold text-[hsl(200,70%,50%)]">{score}/100</span>
              </div>
              {summary?.executive_summary && (
                <p className="text-xs text-muted-foreground mt-3">{String(summary?.executive_summary)}</p>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Tabs: Vulnerabilities, Attack Paths, Endpoints, Logs */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Tabs defaultValue="vulnerabilities">
          <TabsList className="mb-4">
            <TabsTrigger value="vulnerabilities" className="gap-1.5">
              <Bug className="w-3.5 h-3.5" />
              Vulnerabilities ({vulns.length})
            </TabsTrigger>
            <TabsTrigger value="attack-paths" className="gap-1.5">
              <GitBranch className="w-3.5 h-3.5" />
              Attack Paths
            </TabsTrigger>
            <TabsTrigger value="endpoints" className="gap-1.5">
              <Globe className="w-3.5 h-3.5" />
              Discovered Endpoints
            </TabsTrigger>
            <TabsTrigger value="logs" className="gap-1.5">
              <ScrollText className="w-3.5 h-3.5" />
              Agent Logs
            </TabsTrigger>
          </TabsList>

          <TabsContent value="vulnerabilities">
            <Card className="glass-card">
              <CardHeader>
                <CardTitle className="text-base">Findings</CardTitle>
                <p className="text-xs text-muted-foreground">Exploit validation with payload and evidence</p>
              </CardHeader>
              <CardContent>
                {vulns.length === 0 ? (
                  <p className="text-sm text-muted-foreground py-8 text-center">No vulnerabilities reported.</p>
                ) : (
                  <div className="space-y-4">
                    {vulns.map((v, i) => (
                      <VulnCard key={v.id || i} vuln={v} />
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="attack-paths">
            <Card className="glass-card">
              <CardHeader>
                <CardTitle className="text-base">Attack Paths</CardTitle>
              </CardHeader>
              <CardContent>
                {attackPaths.length === 0 ? (
                  <p className="text-sm text-muted-foreground py-8 text-center">No attack paths generated.</p>
                ) : (
                  <div className="space-y-4">
                    {attackPaths.map((path, i) => (
                      <div key={i} className="rounded-lg border border-white/10 p-4">
                        <p className="text-sm font-medium mb-2">{path.title}</p>
                        <div className="flex flex-wrap gap-2">
                          {path.nodes?.map((n) => (
                            <Badge key={n.id} variant="outline" className="text-xs">
                              {n.label}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="endpoints">
            <Card className="glass-card">
              <CardHeader>
                <CardTitle className="text-base">Discovered endpoints</CardTitle>
              </CardHeader>
              <CardContent>
                {!results?.discovered_endpoints ? (
                  <p className="text-sm text-muted-foreground py-8 text-center">No crawl data yet.</p>
                ) : (
                  <div className="space-y-2 text-xs">
                    {(results.discovered_endpoints.pages as any[])?.length > 0 && (
                      <div>
                        <p className="text-muted-foreground mb-1">Pages</p>
                        <ScrollArea className="h-40 rounded border border-white/10 p-2">
                          {(results.discovered_endpoints.pages as any[]).map((p: any, i: number) => (
                            <div key={i} className="py-1 truncate">{p.url} ({p.status})</div>
                          ))}
                        </ScrollArea>
                      </div>
                    )}
                    {(results.discovered_endpoints.forms as any[])?.length > 0 && (
                      <div>
                        <p className="text-muted-foreground mb-1">Forms</p>
                        <ScrollArea className="h-32 rounded border border-white/10 p-2">
                          {(results.discovered_endpoints.forms as any[]).map((f: any, i: number) => (
                            <div key={i} className="py-1">{f.method} {f.action}</div>
                          ))}
                        </ScrollArea>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="logs">
            <Card className="glass-card">
              <CardHeader>
                <CardTitle className="text-base">Agent logs</CardTitle>
              </CardHeader>
              <CardContent>
                {agentLogs.length === 0 ? (
                  <p className="text-sm text-muted-foreground py-8 text-center">No logs yet.</p>
                ) : (
                  <ScrollArea className="h-[400px] pr-4">
                    <div className="space-y-2">
                      {agentLogs.map((log, i) => (
                        <div key={i} className="rounded border border-white/10 p-2 text-xs">
                          <span className="text-cyan-400">{log.agent_name}</span>
                          <span className="text-muted-foreground ml-2">{log.message}</span>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
}

function VulnCard({ vuln }: { vuln: UrlScanVulnerability }) {
  const [open, setOpen] = useState(false);
  const sev = vuln.severity?.toLowerCase() || "medium";
  const sevColor =
    sev === "critical" ? "border-red-500/40 bg-red-500/10" :
      sev === "high" ? "border-orange-500/40 bg-orange-500/10" :
        sev === "medium" ? "border-amber-500/40 bg-amber-500/10" :
          "border-white/20 bg-white/5";
  return (
    <div className={`rounded-lg border p-4 ${sevColor}`}>
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-medium text-sm">{vuln.title}</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            {vuln.endpoint} • {vuln.parameter}
          </p>
        </div>
        <Badge
          variant="outline"
          className={
            sev === "critical" ? "border-red-500/50 text-red-400" :
            sev === "high" ? "border-orange-500/50 text-orange-400" :
            sev === "medium" ? "border-amber-500/50 text-amber-400" :
            "border-white/30 text-muted-foreground"
          }
        >
          {vuln.severity}
        </Badge>
      </div>
      <p className="text-xs text-muted-foreground mt-2">{vuln.description}</p>
      <Button
        variant="ghost"
        size="sm"
        className="mt-2 text-xs"
        onClick={() => setOpen(!open)}
      >
        {open ? "Hide" : "Show"} evidence & patch
      </Button>
      {open && (
        <div className="mt-3 space-y-2 text-xs border-t border-white/10 pt-3">
          <div>
            <span className="text-muted-foreground">Payload: </span>
            <code className="bg-black/30 px-1 rounded">{vuln.payload}</code>
          </div>
          {vuln.evidence && (
            <div>
              <span className="text-muted-foreground">Evidence: </span>
              <p className="mt-1 break-all">{vuln.evidence.slice(0, 400)}{vuln.evidence.length > 400 ? "…" : ""}</p>
            </div>
          )}
          {vuln.impact && (
            <div>
              <span className="text-muted-foreground">Impact: </span>
              {vuln.impact}
            </div>
          )}
          {vuln.patch_recommendation && (
            <div>
              <span className="text-muted-foreground">Patch: </span>
              {vuln.patch_recommendation}
            </div>
          )}
          {vuln.why_missed && (
            <div>
              <span className="text-muted-foreground">Why missed: </span>
              {vuln.why_missed}
            </div>
          )}
          <p className="text-muted-foreground">Confidence: {vuln.confidence}% • Risk score: {vuln.risk_score}</p>
        </div>
      )}
    </div>
  );
}
