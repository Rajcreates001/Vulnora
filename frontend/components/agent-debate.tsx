"use client";

import { motion } from "framer-motion";
import { Brain, MessageSquare, Shield, AlertTriangle, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { DebateMessage } from "@/lib/api";

const agentIcons: Record<string, typeof Brain> = {
  "Resume Analyst": Brain,
  "Technical Depth Analyst": Brain,
  "Behavioral Psychologist": Brain,
  "Domain Expert": Brain,
  "Hiring Manager": Brain,
  "Contradiction Detector": AlertTriangle,
  "Bias Auditor": Shield,
  "Consensus Negotiator": MessageSquare,
};

const agentColors: Record<string, string> = {
  "Resume Analyst": "from-blue-500 to-cyan-500",
  "Technical Depth Analyst": "from-purple-500 to-pink-500",
  "Behavioral Psychologist": "from-green-500 to-emerald-500",
  "Domain Expert": "from-orange-500 to-amber-500",
  "Hiring Manager": "from-indigo-500 to-violet-500",
  "Contradiction Detector": "from-red-500 to-rose-500",
  "Bias Auditor": "from-teal-500 to-cyan-500",
  "Consensus Negotiator": "from-slate-400 to-zinc-500",
};

const stanceColors: Record<string, string> = {
  hire: "text-emerald-400 bg-emerald-500/15 border-emerald-500/30",
  no_hire: "text-red-400 bg-red-500/15 border-red-500/30",
  "no hire": "text-red-400 bg-red-500/15 border-red-500/30",
  conditional: "text-amber-400 bg-amber-500/15 border-amber-500/30",
};

interface AgentDebatePanelProps {
  debate: DebateMessage[];
}

export function AgentDebatePanel({ debate }: AgentDebatePanelProps) {
  if (!debate || debate.length === 0) {
    return (
      <Card className="glass-card">
        <CardContent className="py-12 text-center">
          <MessageSquare className="w-10 h-10 text-muted-foreground mx-auto mb-3 opacity-40" />
          <p className="text-muted-foreground">No debate data available.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass-card">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-primary" />
          Agent Debate Timeline
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[500px] pr-4">
          <div className="space-y-4">
            {debate.map((msg, i) => {
              const Icon = agentIcons[msg.agent_name] || Brain;
              const gradient = agentColors[msg.agent_name] || "from-slate-500 to-slate-600";
              const stanceClass = stanceColors[msg.stance] || stanceColors.conditional;

              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="relative pl-8"
                >
                  {/* Timeline line */}
                  {i < debate.length - 1 && (
                    <div className="absolute left-[15px] top-10 bottom-0 w-px bg-border" />
                  )}

                  {/* Agent icon */}
                  <div
                    className={`absolute left-0 top-1 w-8 h-8 rounded-full bg-gradient-to-br ${gradient} flex items-center justify-center`}
                  >
                    <Icon className="w-4 h-4 text-white" />
                  </div>

                  <div className="glass-card p-4 ml-2">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm font-semibold">{msg.agent_name}</span>
                      <Badge className={stanceClass}>
                        {msg.stance}
                      </Badge>
                      {msg.responding_to && (
                        <span className="text-xs text-muted-foreground flex items-center gap-1">
                          <ChevronRight className="w-3 h-3" />
                          replying to {msg.responding_to}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {msg.message}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
