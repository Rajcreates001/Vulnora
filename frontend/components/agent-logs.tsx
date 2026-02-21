"use client";

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { ScrollText, ChevronDown, ChevronUp, Bot, Filter } from "lucide-react";

interface AgentLog {
  id: string;
  agent_name: string;
  stage: string;
  message: string;
  data?: any;
  created_at: string;
}

const AGENT_COLORS: Record<string, string> = {
  recon: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  static_analysis: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
  vulnerability: "bg-red-500/20 text-red-400 border-red-500/30",
  exploit: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  patch: "bg-green-500/20 text-green-400 border-green-500/30",
  risk: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  alert_reduction: "bg-pink-500/20 text-pink-400 border-pink-500/30",
  insight: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  missed_vuln_reasoning: "bg-lime-500/20 text-lime-400 border-lime-500/30",
  debate: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  report: "bg-indigo-500/20 text-indigo-400 border-indigo-500/30",
};

function getAgentColor(name: string): string {
  const lower = name.toLowerCase();
  for (const [key, color] of Object.entries(AGENT_COLORS)) {
    if (lower.includes(key)) return color;
  }
  return "bg-muted text-muted-foreground border-border";
}

interface AgentLogsProps {
  logs: AgentLog[];
}

export function AgentLogs({ logs }: AgentLogsProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("all");

  const agents = useMemo(() => {
    const set = new Set<string>();
    logs.forEach((l) => set.add(l.agent_name));
    return Array.from(set);
  }, [logs]);

  const filtered = useMemo(() => {
    if (filter === "all") return logs;
    return logs.filter((l) => l.agent_name === filter);
  }, [logs, filter]);

  if (!logs?.length) {
    return (
      <Card className="border-border/50 bg-card/50">
        <CardContent className="flex items-center justify-center py-16 text-muted-foreground">
          <div className="text-center">
            <ScrollText className="h-10 w-10 mx-auto mb-3 opacity-30" />
            <p className="text-sm">No agent logs available</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-border/50 bg-card/50">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Bot className="h-5 w-5 text-indigo-400" />
            Agent Decision Logs
          </CardTitle>
          <div className="flex items-center gap-1 flex-wrap">
            <Button
              variant={filter === "all" ? "default" : "ghost"}
              size="sm"
              className="h-7 text-xs"
              onClick={() => setFilter("all")}
            >
              <Filter className="h-3 w-3 mr-1" />
              All
            </Button>
            {agents.map((agent) => (
              <Button
                key={agent}
                variant={filter === agent ? "default" : "ghost"}
                size="sm"
                className="h-7 text-xs"
                onClick={() => setFilter(agent)}
              >
                {agent.replace(/_/g, " ")}
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[500px]">
          <div className="space-y-1 p-4">
            <AnimatePresence mode="popLayout">
              {filtered.map((log, i) => (
                <motion.div
                  key={log.id}
                  layout
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.2, delay: i * 0.02 }}
                >
                  <div
                    className="rounded-lg border border-border/40 bg-background/50 hover:bg-background/80 transition-colors cursor-pointer"
                    onClick={() =>
                      setExpandedId(expandedId === log.id ? null : log.id)
                    }
                  >
                    <div className="flex items-center gap-3 px-3 py-2">
                      <Badge
                        variant="outline"
                        className={`text-[10px] font-mono ${getAgentColor(log.agent_name)}`}
                      >
                        {log.agent_name}
                      </Badge>
                      <span className="text-xs text-muted-foreground flex-1 truncate">
                        {log.message}
                      </span>
                      <span className="text-[10px] text-muted-foreground/60 whitespace-nowrap">
                        {log.created_at
                          ? new Date(log.created_at).toLocaleTimeString()
                          : ""}
                      </span>
                      {log.data && (
                        expandedId === log.id ? (
                          <ChevronUp className="h-3.5 w-3.5 text-muted-foreground" />
                        ) : (
                          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
                        )
                      )}
                    </div>
                    <AnimatePresence>
                      {expandedId === log.id && log.data && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="overflow-hidden"
                        >
                          <div className="px-3 pb-3 pt-1 border-t border-border/30">
                            <pre className="text-[10px] text-muted-foreground font-mono bg-background rounded p-2 overflow-x-auto max-h-[200px]">
                              {typeof log.data === "string"
                                ? log.data
                                : JSON.stringify(log.data, null, 2)}
                            </pre>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
