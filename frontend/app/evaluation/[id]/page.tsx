"use client";

import { Suspense, useEffect, useState, useRef } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { motion, AnimatePresence, useInView } from "framer-motion";
import Link from "next/link";
import {
  Brain,
  ArrowLeft,
  FileText,
  Mic,
  BarChart3,
  MessageSquare,
  AlertTriangle,
  Target,
  Shield,
  XCircle,
  Loader2,
  CheckCircle2,
  TrendingUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import { useAppStore } from "@/store/useAppStore";
import {
  getCandidate,
  getResults,
  getAgentLogs,
} from "@/lib/api";
import {
  getScoreColor,
  getVerdictColor,
  getVerdictBgColor,
  formatScore,
} from "@/lib/utils";
import type { CandidateDetail, Evaluation, AgentLog } from "@/lib/api";

import {
  SkillRadarChart,
  ScoreBarChart,
  ConfidenceMeter,
  RiskGauge,
  AgentAgreementChart,
} from "@/components/charts";
import { AgentDebatePanel } from "@/components/agent-debate";
import { ContradictionPanel } from "@/components/contradictions";
import { WhyNotHirePanel } from "@/components/why-not-hire";
import { SkillGapPanel } from "@/components/skill-gap";
import { AgentLogsPanel } from "@/components/agent-logs";
import { LiveEvaluation } from "@/components/live-evaluation";

function AnimatedCounter({ value, duration = 1.2 }: { value: number; duration?: number }) {
  const [display, setDisplay] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true });

  useEffect(() => {
    if (!inView) return;
    let start = 0;
    const step = Math.max(1, Math.ceil(value / (duration * 60)));
    const timer = setInterval(() => {
      start += step;
      if (start >= value) { setDisplay(value); clearInterval(timer); }
      else setDisplay(start);
    }, 1000 / 60);
    return () => clearInterval(timer);
  }, [value, inView, duration]);

  return <span ref={ref}>{display}</span>;
}

function ScoreCard({
  label,
  score,
  icon: Icon,
  delay = 0,
}: {
  label: string;
  score: number;
  icon: typeof Brain;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 300, damping: 30, delay }}
    >
      <Card className="glass-card-hover group">
        <CardContent className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <motion.div whileHover={{ rotate: 15 }} transition={{ type: "spring" }}>
              <Icon className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
            </motion.div>
            <span className="text-xs text-muted-foreground">{label}</span>
          </div>
          <div className="flex items-end gap-2">
            <span className={`text-2xl font-bold ${getScoreColor(score)}`}>
              <AnimatedCounter value={score} />
            </span>
            <span className="text-xs text-muted-foreground mb-1">/100</span>
          </div>
          <Progress
            value={score}
            className="mt-2 h-1.5"
            indicatorClassName={
              score >= 80
                ? "bg-emerald-500"
                : score >= 60
                ? "bg-amber-500"
                : score >= 40
                ? "bg-orange-500"
                : "bg-red-500"
            }
          />
        </CardContent>
      </Card>
    </motion.div>
  );
}

function EvaluationPageInner() {
  const params = useParams();
  const searchParams = useSearchParams();
  const candidateId = params.id as string;
  const isLive = searchParams.get("live") === "true";

  const [candidate, setCandidate] = useState<CandidateDetail | null>(null);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [logs, setLogs] = useState<AgentLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [liveMode, setLiveMode] = useState(isLive);

  useEffect(() => {
    loadData();
  }, [candidateId, liveMode]);

  async function loadData() {
    setLoading(true);
    try {
      const candidateData = await getCandidate(candidateId);
      setCandidate(candidateData);

      if (!liveMode) {
        const [evalData, logData] = await Promise.all([
          getResults(candidateId).catch(() => null),
          getAgentLogs(candidateId).catch(() => []),
        ]);
        setEvaluation(evalData);
        setLogs(logData);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  async function handleLiveComplete() {
    setLiveMode(false);
    // Brief delay to allow backend to finish saving
    await new Promise((r) => setTimeout(r, 1500));
    await loadData();
  }

  function handleLiveError(msg: string) {
    setError(msg);
    setLiveMode(false);
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center"
        >
          <div className="relative w-20 h-20 mx-auto mb-4">
            <motion.div
              className="absolute inset-0 rounded-full border-2 border-primary/30"
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            />
            <motion.div
              className="absolute inset-2 rounded-full border-2 border-t-primary border-r-transparent border-b-transparent border-l-transparent"
              animate={{ rotate: -360 }}
              transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
            />
            <Brain className="absolute inset-0 m-auto w-8 h-8 text-primary animate-pulse-slow" />
          </div>
          <p className="text-muted-foreground">Loading intelligence panel...</p>
        </motion.div>
      </div>
    );
  }

  if (error || !candidate) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Card className="glass-card p-8 text-center max-w-md">
          <XCircle className="w-12 h-12 text-destructive mx-auto mb-4" />
          <p className="text-destructive font-medium mb-2">Error</p>
          <p className="text-muted-foreground text-sm">{error || "Candidate not found"}</p>
          <Link href="/dashboard">
            <Button variant="outline" className="mt-4">
              <ArrowLeft className="w-4 h-4 mr-1" />
              Back to Dashboard
            </Button>
          </Link>
        </Card>
      </div>
    );
  }

  const e = evaluation;
  const scoreBarData = e
    ? [
        { name: "Technical", score: e.technical_score },
        { name: "Behavioral", score: e.behavior_score },
        { name: "Domain", score: e.domain_score },
        { name: "Communication", score: e.communication_score },
        { name: "Learning", score: e.learning_potential },
      ]
    : [];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-xl border-b border-border/50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/dashboard">
              <Button variant="ghost" size="icon">
                <ArrowLeft className="w-4 h-4" />
              </Button>
            </Link>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <div>
                <span className="text-sm font-bold">{candidate.name}</span>
                <p className="text-xs text-muted-foreground">Evaluation Report</p>
              </div>
            </div>
          </div>
          {e && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ type: "spring", stiffness: 300, damping: 30 }} className="flex items-center gap-2">
              {(() => {
                const d = e.final_decision.toLowerCase();
                let colors = "border-slate-500/30 bg-slate-500/10 text-slate-400";
                let label = e.final_decision;
                if (d.includes("strong hire")) {
                  colors = "border-emerald-500/30 bg-emerald-500/15 text-emerald-400";
                  label = "Strong Hire";
                } else if (d.includes("hire") && !d.includes("not")) {
                  colors = "border-blue-500/30 bg-blue-500/15 text-blue-400";
                  label = "Hire";
                } else if (d.includes("hold") || d.includes("conditional")) {
                  colors = "border-amber-500/30 bg-amber-500/15 text-amber-400";
                  label = "Hold";
                } else if (d.includes("reject") || d.includes("not") || d.includes("no hire")) {
                  colors = "border-red-500/30 bg-red-500/15 text-red-400";
                  label = "Reject";
                }
                return (
                  <motion.div
                    initial={{ scale: 0.8 }}
                    animate={{ scale: 1 }}
                    transition={{ type: "spring", stiffness: 500, damping: 25 }}
                    className={`px-4 py-1.5 rounded-full border font-semibold text-sm ${colors}`}>
                    {label}
                  </motion.div>
                );
              })()}
              <Badge variant="outline" className="text-xs font-mono">
                Confidence: {e.confidence}%
              </Badge>
            </motion.div>
          )}
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {liveMode ? (
          <LiveEvaluation
            candidateId={candidateId}
            candidateName={candidate.name}
            onComplete={handleLiveComplete}
            onError={handleLiveError}
          />
        ) : !e ? (
          <Card className="glass-card p-12 text-center">
            <Loader2 className="w-12 h-12 text-muted-foreground mx-auto mb-4 opacity-40" />
            <p className="text-muted-foreground">No evaluation results yet.</p>
            <Link href="/dashboard">
              <Button variant="outline" className="mt-4">
                Run Evaluation from Dashboard
              </Button>
            </Link>
          </Card>
        ) : (
          <Tabs defaultValue="overview" className="space-y-6">
            <TabsList className="bg-muted/50 p-1">
              <TabsTrigger value="overview" className="text-xs">
                <BarChart3 className="w-3.5 h-3.5 mr-1" />
                Overview
              </TabsTrigger>
              <TabsTrigger value="debate" className="text-xs">
                <MessageSquare className="w-3.5 h-3.5 mr-1" />
                Agent Debate
              </TabsTrigger>
              <TabsTrigger value="contradictions" className="text-xs">
                <AlertTriangle className="w-3.5 h-3.5 mr-1" />
                Contradictions
              </TabsTrigger>
              <TabsTrigger value="skills" className="text-xs">
                <Target className="w-3.5 h-3.5 mr-1" />
                Skill Gaps
              </TabsTrigger>
              <TabsTrigger value="whynot" className="text-xs">
                <XCircle className="w-3.5 h-3.5 mr-1" />
                Why Not Hire
              </TabsTrigger>
              <TabsTrigger value="documents" className="text-xs">
                <FileText className="w-3.5 h-3.5 mr-1" />
                Documents
              </TabsTrigger>
              <TabsTrigger value="logs" className="text-xs">
                <Shield className="w-3.5 h-3.5 mr-1" />
                Agent Logs
              </TabsTrigger>
            </TabsList>

            {/* ─── Overview Tab ─── */}
            <TabsContent value="overview">
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.4 }}
                className="space-y-6"
              >
                {/* Score Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
                  <ScoreCard label="Technical" score={e.technical_score} icon={Brain} delay={0} />
                  <ScoreCard label="Behavioral" score={e.behavior_score} icon={Brain} delay={0.05} />
                  <ScoreCard label="Domain" score={e.domain_score} icon={Target} delay={0.1} />
                  <ScoreCard label="Communication" score={e.communication_score} icon={Mic} delay={0.15} />
                  <ScoreCard label="Learning" score={e.learning_potential} icon={TrendingUp} delay={0.2} />
                  <ScoreCard label="Confidence" score={e.confidence} icon={CheckCircle2} delay={0.25} />
                  <ScoreCard label="Risk" score={e.risk_score} icon={AlertTriangle} delay={0.3} />
                </div>

                {/* Charts Row */}
                <div className="grid md:grid-cols-3 gap-4">
                  <ConfidenceMeter
                    confidence={e.confidence}
                    decision={e.final_decision}
                  />
                  <SkillRadarChart
                    data={{
                      technical: e.technical_score,
                      behavior: e.behavior_score,
                      domain: e.domain_score,
                      communication: e.communication_score,
                      risk: 100 - e.risk_score,
                      learning: e.learning_potential,
                    }}
                  />
                  <RiskGauge
                    riskScore={e.risk_score}
                    attritionRisk={e.risk_analysis?.attrition_risk || 0}
                  />
                </div>

                {/* Score Bar + Agent Agreement */}
                <div className="grid md:grid-cols-2 gap-4">
                  <ScoreBarChart scores={scoreBarData} />
                  {e.scores_json && (
                    <AgentAgreementChart
                      opinions={
                        (e.scores_json as any)?.agent_opinions?.length
                          ? (e.scores_json as any).agent_opinions
                          : [
                              { agent_name: "Resume Analyst", decision: e.final_decision, confidence: e.technical_score },
                              { agent_name: "Technical", decision: e.final_decision, confidence: e.technical_score },
                              { agent_name: "Behavioral", decision: e.final_decision, confidence: e.behavior_score },
                              { agent_name: "Domain", decision: e.final_decision, confidence: e.domain_score },
                              { agent_name: "Manager", decision: e.final_decision, confidence: e.confidence },
                            ]
                      }
                    />
                  )}
                </div>

                {/* Reasoning */}
                {e.reasoning && (
                  <Card className="glass-card">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <Brain className="w-4 h-4 text-primary" />
                        Decision Reasoning
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-sm text-muted-foreground leading-relaxed space-y-3">
                        {e.reasoning.split('\n').filter(Boolean).map((paragraph, idx) => {
                          // Check if it's a section header (CANDIDATE PROFILE:, TECHNICAL ASSESSMENT:, etc.)
                          const headerMatch = paragraph.match(/^([A-Z][A-Z\s]+):\s*(.*)/);
                          if (headerMatch) {
                            return (
                              <div key={idx}>
                                <p className="text-xs font-semibold text-foreground uppercase tracking-wider mt-3 mb-1">
                                  {headerMatch[1]}
                                </p>
                                <p>{headerMatch[2]}</p>
                              </div>
                            );
                          }
                          return <p key={idx}>{paragraph}</p>;
                        })}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Risk Analysis Details */}
                {e.risk_analysis && (
                  <Card className="glass-card">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <Shield className="w-4 h-4 text-primary" />
                        Risk Analysis
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid md:grid-cols-2 gap-6">
                        <div>
                          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                            Risk Factors
                          </p>
                          {e.risk_analysis.risk_factors.map((f, i) => (
                            <div key={i} className="flex items-start gap-2 text-sm mb-1">
                              <AlertTriangle className="w-3 h-3 mt-1 text-amber-400 shrink-0" />
                              <span className="text-muted-foreground">{f}</span>
                            </div>
                          ))}
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                            Mitigating Factors
                          </p>
                          {e.risk_analysis.mitigating_factors.map((f, i) => (
                            <div key={i} className="flex items-start gap-2 text-sm mb-1">
                              <CheckCircle2 className="w-3 h-3 mt-1 text-emerald-400 shrink-0" />
                              <span className="text-muted-foreground">{f}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </motion.div>
            </TabsContent>

            {/* ─── Agent Debate Tab ─── */}
            <TabsContent value="debate">
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
                <AgentDebatePanel debate={e.agent_debate || []} />
              </motion.div>
            </TabsContent>

            {/* ─── Contradictions Tab ─── */}
            <TabsContent value="contradictions">
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
                <ContradictionPanel contradictions={e.contradictions || []} />
              </motion.div>
            </TabsContent>

            {/* ─── Skill Gaps Tab ─── */}
            <TabsContent value="skills">
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
                <SkillGapPanel gaps={e.skill_gaps || []} />
              </motion.div>
            </TabsContent>

            {/* ─── Why Not Hire Tab ─── */}
            <TabsContent value="whynot">
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
                <WhyNotHirePanel
                  data={e.why_not_hire}
                  roadmap={e.improvement_roadmap}
                  decision={e.final_decision}
                />
              </motion.div>
            </TabsContent>

            {/* ─── Documents Tab ─── */}
            <TabsContent value="documents">
              <div className="grid md:grid-cols-2 gap-4">
                <Card className="glass-card">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                      <FileText className="w-4 h-4 text-primary" />
                      Resume
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ScrollArea className="h-[500px]">
                      <pre className="text-xs text-muted-foreground whitespace-pre-wrap font-mono leading-relaxed">
                        {candidate.resume_text}
                      </pre>
                    </ScrollArea>
                  </CardContent>
                </Card>
                <Card className="glass-card">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                      <Mic className="w-4 h-4 text-primary" />
                      Interview Transcript
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ScrollArea className="h-[500px]">
                      <pre className="text-xs text-muted-foreground whitespace-pre-wrap font-mono leading-relaxed">
                        {candidate.transcript_text}
                      </pre>
                    </ScrollArea>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* ─── Agent Logs Tab ─── */}
            <TabsContent value="logs">
              <AgentLogsPanel logs={logs} />
            </TabsContent>
          </Tabs>
        )}
      </main>
    </div>
  );
}

export default function EvaluationPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-background flex items-center justify-center">
          <div className="text-center">
            <Brain className="w-10 h-10 text-primary mx-auto mb-3 animate-pulse" />
            <p className="text-muted-foreground text-sm">Loading...</p>
          </div>
        </div>
      }
    >
      <EvaluationPageInner />
    </Suspense>
  );
}
