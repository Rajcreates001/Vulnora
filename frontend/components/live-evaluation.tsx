"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Brain,
  CheckCircle2,
  Loader2,
  AlertCircle,
  MessageSquare,
  Zap,
  Shield,
  AlertTriangle,
  Target,
  Users,
  Eye,
  BarChart3,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

// ──────────── Types ────────────

interface StreamEvent {
  type: string;
  agent_name?: string;
  message?: string;
  step?: number;
  total_steps?: number;
  phase?: string;
  role?: string;
  data?: any;
  evaluation_id?: string;
  candidate_id?: string;
  final_decision?: string;
  confidence?: number;
}

interface AgentMessage {
  id: number;
  agent_name: string;
  message: string;
  phase: string;
  type: "start" | "message" | "debate" | "score" | "complete";
  stance?: string;
  responding_to?: string;
  timestamp: Date;
}

// ──────────── Agent Visual Config ────────────

const agentConfig: Record<
  string,
  { gradient: string; icon: typeof Brain; shortName: string }
> = {
  System: { gradient: "from-slate-500 to-zinc-600", icon: Zap, shortName: "SYS" },
  "Resume Analyst": { gradient: "from-blue-500 to-cyan-500", icon: Eye, shortName: "RA" },
  "Technical Depth Analyst": { gradient: "from-purple-500 to-pink-500", icon: Brain, shortName: "TD" },
  "Behavioral Psychologist": { gradient: "from-green-500 to-emerald-500", icon: Users, shortName: "BP" },
  "Domain Expert": { gradient: "from-orange-500 to-amber-500", icon: Target, shortName: "DE" },
  "Contradiction Detector": { gradient: "from-red-500 to-rose-500", icon: AlertTriangle, shortName: "CD" },
  "Hiring Manager": { gradient: "from-indigo-500 to-violet-500", icon: BarChart3, shortName: "HM" },
  "Bias Auditor": { gradient: "from-teal-500 to-cyan-500", icon: Shield, shortName: "BA" },
  "Consensus Negotiator": { gradient: "from-yellow-500 to-orange-500", icon: MessageSquare, shortName: "CN" },
};

const PIPELINE_AGENTS = [
  "Resume Analyst",
  "Technical Depth Analyst",
  "Behavioral Psychologist",
  "Domain Expert",
  "Contradiction Detector",
  "Hiring Manager",
  "Bias Auditor",
  "Consensus Negotiator",
];

// ──────────── Component ────────────

interface LiveEvaluationProps {
  candidateId: string;
  candidateName: string;
  onComplete: (evaluationId: string) => void;
  onError: (error: string) => void;
}

export function LiveEvaluation({
  candidateId,
  candidateName,
  onComplete,
  onError,
}: LiveEvaluationProps) {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [totalSteps, setTotalSteps] = useState(8);
  const [activeAgent, setActiveAgent] = useState<string>("");
  const [completedAgents, setCompletedAgents] = useState<Set<string>>(new Set());
  const [scores, setScores] = useState<any>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const msgIdRef = useRef(0);

  useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const eventSource = new EventSource(
      `${apiBase}/api/run-evaluation-stream/${candidateId}`
    );

    eventSource.onmessage = (event) => {
      const data: StreamEvent = JSON.parse(event.data);

      switch (data.type) {
        case "status":
          setTotalSteps(data.total_steps || 8);
          addMessage({
            agent_name: "System",
            message: data.message || "Starting...",
            phase: "start",
            type: "start",
          });
          break;

        case "agent_start":
          setActiveAgent(data.agent_name || "");
          setCurrentStep(data.step || 0);
          setTotalSteps(data.total_steps || 8);
          addMessage({
            agent_name: data.agent_name || "System",
            message: data.message || "Starting analysis...",
            phase: "start",
            type: "start",
          });
          break;

        case "agent_message":
          addMessage({
            agent_name: data.agent_name || "Unknown",
            message: data.message || "",
            phase: data.phase || "analysis",
            type: "message",
          });
          break;

        case "agent_complete":
          setCurrentStep(data.step || 0);
          if (data.agent_name) {
            setCompletedAgents((prev) => new Set(Array.from(prev).concat(data.agent_name!)));
          }
          break;

        case "scores":
          setScores(data.data);
          break;

        case "debate_message":
          if (data.data) {
            addMessage({
              agent_name: data.data.agent_name || "Unknown",
              message: data.data.message || "",
              phase: "debate",
              type: "debate",
              stance: data.data.stance,
              responding_to: data.data.responding_to,
            });
          }
          break;

        case "complete":
          setIsComplete(true);
          eventSource.close();
          // Small delay to let user see the completion animation
          setTimeout(() => onComplete(data.evaluation_id || ""), 2000);
          break;

        case "error":
          setError(data.message || "Unknown error");
          eventSource.close();
          onError(data.message || "Unknown error");
          break;
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      if (!isComplete) {
        setError("Connection lost. The evaluation may still be running.");
        onError("Connection lost");
      }
    };

    return () => eventSource.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [candidateId]);

  function addMessage(msg: Omit<AgentMessage, "id" | "timestamp">) {
    msgIdRef.current++;
    setMessages((prev) => [
      ...prev,
      { ...msg, id: msgIdRef.current, timestamp: new Date() },
    ]);
    setTimeout(() => {
      scrollRef.current?.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth",
      });
    }, 100);
  }

  const progress = totalSteps > 0 ? (currentStep / totalSteps) * 100 : 0;

  return (
    <div className="space-y-6">
      {/* ── Pipeline Progress ── */}
      <Card className="glass-card overflow-hidden">
        <CardContent className="p-6">
          {/* Header row */}
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-3">
              <motion.div
                className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center"
                animate={
                  !isComplete
                    ? {
                        boxShadow: [
                          "0 0 0 0 rgba(6,182,212,0)",
                          "0 0 20px 8px rgba(6,182,212,0.3)",
                          "0 0 0 0 rgba(6,182,212,0)",
                        ],
                      }
                    : {}
                }
                transition={{ duration: 2, repeat: Infinity }}
              >
                {isComplete ? (
                  <CheckCircle2 className="w-6 h-6 text-white" />
                ) : (
                  <Brain className="w-6 h-6 text-white" />
                )}
              </motion.div>
              <div>
                <h2 className="text-lg font-bold">
                  {isComplete
                    ? "Evaluation Complete"
                    : "AI Agents Evaluating"}
                </h2>
                <p className="text-sm text-muted-foreground">
                  {isComplete
                    ? `Decision reached for ${candidateName}`
                    : `Processing ${candidateName}`}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-primary">
                {currentStep}/{totalSteps}
              </p>
              <p className="text-xs text-muted-foreground">agents complete</p>
            </div>
          </div>

          {/* Progress bar */}
          <Progress
            value={progress}
            className="h-2"
            indicatorClassName={isComplete ? "bg-emerald-500" : "bg-cyan-500"}
          />

          {/* Agent pipeline icons */}
          <div className="flex items-center justify-between mt-5 gap-1">
            {PIPELINE_AGENTS.map((name) => {
              const cfg = agentConfig[name] || agentConfig.System;
              const Icon = cfg.icon;
              const isDone = completedAgents.has(name);
              const isActive = activeAgent === name && !isDone;

              return (
                <motion.div
                  key={name}
                  className="flex flex-col items-center gap-1.5 flex-1"
                  animate={isActive ? { scale: [1, 1.08, 1] } : {}}
                  transition={
                    isActive ? { duration: 1.5, repeat: Infinity } : {}
                  }
                >
                  <div
                    className={`w-9 h-9 rounded-lg bg-gradient-to-br ${cfg.gradient} flex items-center justify-center transition-all duration-300 ${
                      isDone
                        ? "opacity-100 ring-2 ring-emerald-500/50"
                        : isActive
                        ? "opacity-100 ring-2 ring-cyan-400/50"
                        : "opacity-30"
                    }`}
                  >
                    {isDone ? (
                      <CheckCircle2 className="w-4 h-4 text-white" />
                    ) : isActive ? (
                      <Loader2 className="w-4 h-4 text-white animate-spin" />
                    ) : (
                      <Icon className="w-4 h-4 text-white" />
                    )}
                  </div>
                  <span
                    className={`text-[9px] text-center leading-tight ${
                      isDone || isActive
                        ? "text-foreground"
                        : "text-muted-foreground/50"
                    }`}
                  >
                    {cfg.shortName}
                  </span>
                </motion.div>
              );
            })}
          </div>

          {/* Active agent label */}
          {activeAgent && !isComplete && (
            <motion.div
              className="mt-4 flex items-center gap-2"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
              <span className="text-sm text-cyan-400">
                {activeAgent} is analyzing...
              </span>
            </motion.div>
          )}

          {/* Scores summary (appears after consensus) */}
          {scores && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-5 p-4 rounded-lg bg-muted/30 border border-border/50"
            >
              <div className="flex items-center gap-4 flex-wrap">
                <Badge
                  className={
                    scores.final_decision?.toLowerCase() === "hire"
                      ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
                      : scores.final_decision?.toLowerCase().includes("no")
                      ? "bg-red-500/15 text-red-400 border-red-500/30"
                      : "bg-amber-500/15 text-amber-400 border-amber-500/30"
                  }
                >
                  {scores.final_decision}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  Confidence:{" "}
                  <strong className="text-foreground">{scores.confidence}%</strong>
                </span>
                <span className="text-sm text-muted-foreground">
                  Technical:{" "}
                  <strong className="text-foreground">
                    {scores.technical_score}
                  </strong>
                </span>
                <span className="text-sm text-muted-foreground">
                  Behavioral:{" "}
                  <strong className="text-foreground">
                    {scores.behavior_score}
                  </strong>
                </span>
                <span className="text-sm text-muted-foreground">
                  Domain:{" "}
                  <strong className="text-foreground">
                    {scores.domain_score}
                  </strong>
                </span>
              </div>
            </motion.div>
          )}
        </CardContent>
      </Card>

      {/* ── Live Agent Conversation Feed ── */}
      <Card className="glass-card">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-primary" />
            Live Agent Conversation
            {!isComplete && !error && (
              <span className="relative flex h-2 w-2 ml-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500" />
              </span>
            )}
            {isComplete && (
              <Badge className="ml-auto bg-emerald-500/15 text-emerald-400 border-emerald-500/30">
                Complete
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div
            ref={scrollRef}
            className="h-[500px] overflow-y-auto pr-2 space-y-3"
          >
            <AnimatePresence>
              {messages.map((msg) => {
                const cfg =
                  agentConfig[msg.agent_name] || agentConfig.System;
                const Icon = cfg.icon;

                return (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 15, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ duration: 0.3 }}
                    className={`relative pl-12 ${
                      msg.type === "debate" ? "ml-4" : ""
                    }`}
                  >
                    {/* Agent avatar */}
                    <div
                      className={`absolute left-0 top-1 w-9 h-9 rounded-lg bg-gradient-to-br ${cfg.gradient} flex items-center justify-center shadow-lg`}
                    >
                      {msg.type === "debate" ? (
                        <MessageSquare className="w-4 h-4 text-white" />
                      ) : msg.type === "start" ? (
                        <Zap className="w-4 h-4 text-white" />
                      ) : (
                        <Icon className="w-4 h-4 text-white" />
                      )}
                    </div>

                    <div
                      className={`glass-card p-3 ${
                        msg.type === "debate"
                          ? "border-l-2 border-primary/30"
                          : ""
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-semibold">
                          {msg.agent_name}
                        </span>
                        {msg.type === "start" && (
                          <Badge className="bg-blue-500/15 text-blue-400 border-blue-500/30 text-[10px]">
                            starting
                          </Badge>
                        )}
                        {msg.type === "message" && (
                          <Badge className="bg-emerald-500/15 text-emerald-400 border-emerald-500/30 text-[10px]">
                            analysis
                          </Badge>
                        )}
                        {msg.type === "debate" && msg.stance && (
                          <Badge
                            className={
                              msg.stance === "hire"
                                ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
                                : msg.stance === "no_hire" ||
                                  msg.stance === "no hire"
                                ? "bg-red-500/15 text-red-400 border-red-500/30"
                                : "bg-amber-500/15 text-amber-400 border-amber-500/30"
                            }
                          >
                            {msg.stance}
                          </Badge>
                        )}
                        {msg.responding_to && (
                          <span className="text-[10px] text-muted-foreground">
                            → replying to {msg.responding_to}
                          </span>
                        )}
                        <span className="text-[10px] text-muted-foreground ml-auto">
                          {msg.timestamp.toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground leading-relaxed">
                        {msg.message}
                      </p>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>

            {/* Typing indicator */}
            {!isComplete && !error && activeAgent && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="relative pl-12"
              >
                <div
                  className={`absolute left-0 top-1 w-9 h-9 rounded-lg bg-gradient-to-br ${
                    (agentConfig[activeAgent] || agentConfig.System).gradient
                  } flex items-center justify-center shadow-lg`}
                >
                  <Loader2 className="w-4 h-4 text-white animate-spin" />
                </div>
                <div className="glass-card p-3">
                  <span className="text-sm font-semibold">{activeAgent}</span>
                  <div className="flex gap-1 mt-1.5">
                    <motion.div
                      className="w-1.5 h-1.5 rounded-full bg-muted-foreground"
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{ duration: 1, repeat: Infinity, delay: 0 }}
                    />
                    <motion.div
                      className="w-1.5 h-1.5 rounded-full bg-muted-foreground"
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{
                        duration: 1,
                        repeat: Infinity,
                        delay: 0.3,
                      }}
                    />
                    <motion.div
                      className="w-1.5 h-1.5 rounded-full bg-muted-foreground"
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{
                        duration: 1,
                        repeat: Infinity,
                        delay: 0.6,
                      }}
                    />
                  </div>
                </div>
              </motion.div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Error display */}
      {error && (
        <Card className="glass-card border-destructive/30">
          <CardContent className="p-4 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-destructive shrink-0" />
            <p className="text-sm text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Completion message */}
      {isComplete && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="glass-card border-emerald-500/30">
            <CardContent className="p-4 flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
              <p className="text-sm text-emerald-400">
                Evaluation complete! Loading full results...
              </p>
              <Loader2 className="w-4 h-4 text-emerald-400 animate-spin ml-auto" />
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
