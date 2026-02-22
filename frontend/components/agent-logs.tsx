"use client";

import { motion } from "framer-motion";
import { Brain, Clock, FileText } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { AgentLog } from "@/lib/api";

interface AgentLogsPanelProps {
  logs: AgentLog[];
}

const phaseColors: Record<string, string> = {
  analysis: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  audit: "bg-teal-500/15 text-teal-400 border-teal-500/30",
  debate: "bg-purple-500/15 text-purple-400 border-purple-500/30",
  consensus: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  final: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
};

export function AgentLogsPanel({ logs }: AgentLogsPanelProps) {
  if (!logs || logs.length === 0) {
    return (
      <Card className="glass-card">
        <CardContent className="py-12 text-center">
          <FileText className="w-10 h-10 text-muted-foreground mx-auto mb-3 opacity-40" />
          <p className="text-muted-foreground">No agent logs available.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass-card">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <FileText className="w-4 h-4 text-primary" />
          Agent Reasoning Logs
          <Badge variant="outline" className="ml-auto">
            {logs.length} entries
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[500px] pr-4">
          <div className="space-y-3">
            {logs.map((log, i) => (
              <motion.div
                key={log.id || i}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="glass-card p-3"
              >
                <div className="flex items-center gap-2 mb-1.5">
                  <div className="w-6 h-6 rounded bg-primary/10 flex items-center justify-center">
                    <Brain className="w-3.5 h-3.5 text-primary" />
                  </div>
                  <span className="text-sm font-medium">{log.agent_name}</span>
                  {log.phase && (
                    <Badge className={phaseColors[log.phase] || phaseColors.analysis}>
                      {log.phase}
                    </Badge>
                  )}
                  <span className="text-xs text-muted-foreground ml-auto flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed pl-8">
                  {log.message}
                </p>
              </motion.div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

// Alias for backward compatibility
export const AgentLogs = AgentLogsPanel;
