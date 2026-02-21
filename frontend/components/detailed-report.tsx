"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Shield,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  FileText,
  Target,
  ArrowRight,
  Activity,
  TrendingUp,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ReportData {
  executive_summary: string;
  total_vulnerabilities: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  overall_risk_rating: string;
  overall_risk_score: number;
  key_findings: string[];
  recommendations: string[];
  remediation_priority: Array<{
    title: string;
    priority: string;
    description: string;
  }>;
  conclusion: string;
  generated_at?: string;
}

interface DebateResult {
  vulnerability_title: string;
  red_team_argument: string;
  blue_team_argument: string;
  verdict: string;
  final_reasoning: string;
}

interface DetailedReportProps {
  projectId: string;
}

function getRiskColor(rating: string) {
  switch (rating?.toLowerCase()) {
    case "critical":
      return {
        text: "text-red-400",
        bg: "bg-red-500/10",
        border: "border-red-500/30",
        bar: "bg-red-500",
      };
    case "high":
      return {
        text: "text-orange-400",
        bg: "bg-orange-500/10",
        border: "border-orange-500/30",
        bar: "bg-orange-500",
      };
    case "medium":
      return {
        text: "text-yellow-400",
        bg: "bg-yellow-500/10",
        border: "border-yellow-500/30",
        bar: "bg-yellow-500",
      };
    default:
      return {
        text: "text-green-400",
        bg: "bg-green-500/10",
        border: "border-green-500/30",
        bar: "bg-green-500",
      };
  }
}

function getVerdictIcon(verdict: string) {
  switch (verdict?.toUpperCase()) {
    case "CONFIRMED":
      return <XCircle className="h-4 w-4 text-red-400" />;
    case "LIKELY":
      return <AlertTriangle className="h-4 w-4 text-orange-400" />;
    case "DISPUTED":
      return <Activity className="h-4 w-4 text-yellow-400" />;
    case "FALSE_POSITIVE":
      return <CheckCircle2 className="h-4 w-4 text-green-400" />;
    default:
      return <Activity className="h-4 w-4 text-gray-400" />;
  }
}

function getVerdictColor(verdict: string) {
  switch (verdict?.toUpperCase()) {
    case "CONFIRMED":
      return "text-red-400 bg-red-500/10 border-red-500/30";
    case "LIKELY":
      return "text-orange-400 bg-orange-500/10 border-orange-500/30";
    case "DISPUTED":
      return "text-yellow-400 bg-yellow-500/10 border-yellow-500/30";
    case "FALSE_POSITIVE":
      return "text-green-400 bg-green-500/10 border-green-500/30";
    default:
      return "text-gray-400 bg-gray-500/10 border-gray-500/30";
  }
}

export function DetailedReport({ projectId }: DetailedReportProps) {
  const [report, setReport] = useState<ReportData | null>(null);
  const [debates, setDebates] = useState<DebateResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchReport() {
      try {
        const res = await fetch(`${API_BASE}/api/report/${projectId}`);
        if (res.ok) {
          const data = await res.json();
          setReport(data.report);
          setDebates(data.debate_results || []);
        }
      } catch (e) {
        console.error("Failed to load report:", e);
      } finally {
        setLoading(false);
      }
    }
    fetchReport();
  }, [projectId]);

  if (loading) {
    return (
      <Card className="border-border/50 bg-card/50">
        <CardContent className="flex items-center justify-center py-16 text-muted-foreground">
          <p className="text-sm">Loading report...</p>
        </CardContent>
      </Card>
    );
  }

  if (!report) {
    return (
      <Card className="border-border/50 bg-card/50">
        <CardContent className="flex items-center justify-center py-16 text-muted-foreground">
          <div className="text-center">
            <FileText className="h-10 w-10 mx-auto mb-3 opacity-30" />
            <p className="text-sm">No report available. Run a scan first.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const riskStyle = getRiskColor(report.overall_risk_rating);

  return (
    <div className="space-y-6">
      {/* Overall Risk Card */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Card className={`border ${riskStyle.border} ${riskStyle.bg}`}>
          <CardContent className="py-6">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center gap-4">
                <div
                  className={`flex h-16 w-16 items-center justify-center rounded-2xl ${riskStyle.bg}`}
                >
                  <Shield className={`h-8 w-8 ${riskStyle.text}`} />
                </div>
                <div>
                  <h2 className="text-2xl font-bold">Security Assessment</h2>
                  <p className="text-sm text-muted-foreground mt-1">
                    Overall Risk Level
                  </p>
                </div>
              </div>
              <div className="text-right">
                <Badge
                  variant="outline"
                  className={`text-lg px-4 py-1 ${riskStyle.text} ${riskStyle.border} ${riskStyle.bg}`}
                >
                  {report.overall_risk_rating || "N/A"}
                </Badge>
                {report.overall_risk_score > 0 && (
                  <p className={`text-3xl font-bold mt-1 ${riskStyle.text}`}>
                    {report.overall_risk_score}
                    <span className="text-sm text-muted-foreground">/100</span>
                  </p>
                )}
              </div>
            </div>

            {/* Severity breakdown bar */}
            <div className="mt-6 space-y-2">
              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                <span>
                  {report.total_vulnerabilities} total vulnerabilities
                </span>
              </div>
              <div className="flex h-3 rounded-full overflow-hidden bg-background/50 gap-px">
                {report.critical_count > 0 && (
                  <div
                    className="bg-red-500 rounded-sm"
                    style={{
                      width: `${(report.critical_count / Math.max(report.total_vulnerabilities, 1)) * 100}%`,
                    }}
                  />
                )}
                {report.high_count > 0 && (
                  <div
                    className="bg-orange-500 rounded-sm"
                    style={{
                      width: `${(report.high_count / Math.max(report.total_vulnerabilities, 1)) * 100}%`,
                    }}
                  />
                )}
                {report.medium_count > 0 && (
                  <div
                    className="bg-yellow-500 rounded-sm"
                    style={{
                      width: `${(report.medium_count / Math.max(report.total_vulnerabilities, 1)) * 100}%`,
                    }}
                  />
                )}
                {report.low_count > 0 && (
                  <div
                    className="bg-green-500 rounded-sm"
                    style={{
                      width: `${(report.low_count / Math.max(report.total_vulnerabilities, 1)) * 100}%`,
                    }}
                  />
                )}
              </div>
              <div className="flex gap-4 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <div className="h-2 w-2 rounded-full bg-red-500" />{" "}
                  {report.critical_count} Critical
                </span>
                <span className="flex items-center gap-1">
                  <div className="h-2 w-2 rounded-full bg-orange-500" />{" "}
                  {report.high_count} High
                </span>
                <span className="flex items-center gap-1">
                  <div className="h-2 w-2 rounded-full bg-yellow-500" />{" "}
                  {report.medium_count} Medium
                </span>
                <span className="flex items-center gap-1">
                  <div className="h-2 w-2 rounded-full bg-green-500" />{" "}
                  {report.low_count} Low
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Executive Summary */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
      >
        <Card className="border-border/50 bg-card/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <FileText className="h-5 w-5 text-blue-400" />
              Executive Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-line">
              {report.executive_summary}
            </p>
          </CardContent>
        </Card>
      </motion.div>

      {/* Key Findings */}
      {report.key_findings?.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="border-border/50 bg-card/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <Target className="h-5 w-5 text-red-400" />
                Key Findings
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {report.key_findings.map((finding, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-sm text-muted-foreground"
                  >
                    <AlertTriangle className="h-4 w-4 text-orange-400 mt-0.5 shrink-0" />
                    <span>{finding}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Security Debate Results */}
      {debates?.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <Card className="border-border/50 bg-card/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <Activity className="h-5 w-5 text-purple-400" />
                Security Debate — Why It&apos;s Safe or Not
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {debates.slice(0, 10).map((debate, i) => (
                <div
                  key={i}
                  className="rounded-lg border border-border/40 bg-background/50 p-4 space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-semibold text-foreground">
                      {debate.vulnerability_title}
                    </h4>
                    <Badge
                      variant="outline"
                      className={`text-[10px] gap-1 ${getVerdictColor(debate.verdict)}`}
                    >
                      {getVerdictIcon(debate.verdict)}
                      {debate.verdict}
                    </Badge>
                  </div>

                  {/* Red Team */}
                  <div className="rounded-md border border-red-500/20 bg-red-500/5 p-3">
                    <div className="flex items-center gap-1.5 mb-1">
                      <XCircle className="h-3.5 w-3.5 text-red-400" />
                      <span className="text-xs font-semibold text-red-400">
                        Red Team (Attacker)
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {debate.red_team_argument}
                    </p>
                  </div>

                  {/* Blue Team */}
                  <div className="rounded-md border border-blue-500/20 bg-blue-500/5 p-3">
                    <div className="flex items-center gap-1.5 mb-1">
                      <Shield className="h-3.5 w-3.5 text-blue-400" />
                      <span className="text-xs font-semibold text-blue-400">
                        Blue Team (Defender)
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {debate.blue_team_argument}
                    </p>
                  </div>

                  {/* Final Reasoning */}
                  {debate.final_reasoning && (
                    <div className="rounded-md border border-border/30 bg-background/70 p-3">
                      <div className="flex items-center gap-1.5 mb-1">
                        <TrendingUp className="h-3.5 w-3.5 text-indigo-400" />
                        <span className="text-xs font-semibold text-indigo-400">
                          Final Verdict
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground leading-relaxed">
                        {debate.final_reasoning}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Recommendations */}
      {report.recommendations?.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="border-border/50 bg-card/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-400" />
                Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {report.recommendations.map((rec, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-sm text-muted-foreground"
                  >
                    <ArrowRight className="h-4 w-4 text-green-400 mt-0.5 shrink-0" />
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Remediation Priority */}
      {report.remediation_priority?.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
        >
          <Card className="border-border/50 bg-card/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-yellow-400" />
                Remediation Priority
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {report.remediation_priority.map((item, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3 rounded-lg border border-border/40 bg-background/50 p-3"
                >
                  <Badge
                    variant="outline"
                    className={`text-[10px] shrink-0 ${
                      item.priority === "Immediate"
                        ? "text-red-400 border-red-500/30"
                        : item.priority === "Short-term"
                        ? "text-yellow-400 border-yellow-500/30"
                        : "text-green-400 border-green-500/30"
                    }`}
                  >
                    {item.priority}
                  </Badge>
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {item.title}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {item.description}
                    </p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Conclusion */}
      {report.conclusion && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className={`border ${riskStyle.border} ${riskStyle.bg}`}>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <Shield className={`h-5 w-5 ${riskStyle.text}`} />
                Conclusion
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-foreground/80 leading-relaxed whitespace-pre-line">
                {report.conclusion}
              </p>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
