"use client";

import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Search,
  Shield,
  Bug,
  Swords,
  Wrench,
  BarChart3,
  MessageSquare,
  FileText,
  Radio,
  Bot,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ChatMessage {
  id: string;
  agent: string;
  message: string;
  message_type: string;
  timestamp: number;
  type: string;
}

const AGENT_CONFIG: Record<
  string,
  { label: string; icon: any; color: string; bgColor: string; borderColor: string }
> = {
  recon_agent: {
    label: "Recon Agent",
    icon: Search,
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/30",
  },
  static_analysis_agent: {
    label: "Static Analysis",
    icon: Shield,
    color: "text-cyan-400",
    bgColor: "bg-cyan-500/10",
    borderColor: "border-cyan-500/30",
  },
  vulnerability_discovery_agent: {
    label: "Vuln Discovery",
    icon: Bug,
    color: "text-red-400",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/30",
  },
  exploit_simulation_agent: {
    label: "Exploit Simulator",
    icon: Swords,
    color: "text-orange-400",
    bgColor: "bg-orange-500/10",
    borderColor: "border-orange-500/30",
  },
  patch_generation_agent: {
    label: "Patch Generator",
    icon: Wrench,
    color: "text-green-400",
    bgColor: "bg-green-500/10",
    borderColor: "border-green-500/30",
  },
  risk_prioritization_agent: {
    label: "Risk Scorer",
    icon: BarChart3,
    color: "text-yellow-400",
    bgColor: "bg-yellow-500/10",
    borderColor: "border-yellow-500/30",
  },
  security_debate_agent: {
    label: "Debate Agent",
    icon: MessageSquare,
    color: "text-purple-400",
    bgColor: "bg-purple-500/10",
    borderColor: "border-purple-500/30",
  },
  report_generation_agent: {
    label: "Report Generator",
    icon: FileText,
    color: "text-indigo-400",
    bgColor: "bg-indigo-500/10",
    borderColor: "border-indigo-500/30",
  },
  alert_reduction_agent: {
    label: "Alert Reduction",
    icon: MessageSquare,
    color: "text-pink-400",
    bgColor: "bg-pink-500/10",
    borderColor: "border-pink-500/30",
  },
  insight_agent: {
    label: "Insight Agent",
    icon: FileText,
    color: "text-amber-400",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/30",
  },
  missed_vuln_reasoning_agent: {
    label: "Missed Vuln Reasoning",
    icon: MessageSquare,
    color: "text-lime-400",
    bgColor: "bg-lime-500/10",
    borderColor: "border-lime-500/30",
  },
  system: {
    label: "System",
    icon: Bot,
    color: "text-gray-400",
    bgColor: "bg-gray-500/10",
    borderColor: "border-gray-500/30",
  },
};

function getAgentConfig(name: string) {
  return (
    AGENT_CONFIG[name] || {
      label: name.replace(/_/g, " "),
      icon: Bot,
      color: "text-gray-400",
      bgColor: "bg-gray-500/10",
      borderColor: "border-gray-500/30",
    }
  );
}

interface LiveAgentChatProps {
  projectId: string;
  isScanning: boolean;
}

export function LiveAgentChat({ projectId, isScanning }: LiveAgentChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const msgIdRef = useRef(0);

  useEffect(() => {
    if (!isScanning) return;

    const es = new EventSource(`${API_BASE}/api/scan-stream/${projectId}`);
    eventSourceRef.current = es;

    es.onopen = () => setConnected(true);

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "ping" || data.type === "connected") return;
        if (data.type === "done") {
          setConnected(false);
          es.close();
          return;
        }

        const chatMsg: ChatMessage = {
          id: `msg_${++msgIdRef.current}`,
          agent: data.agent || "system",
          message: data.message || "",
          message_type: data.message_type || data.status || "info",
          timestamp: data.timestamp || Date.now() / 1000,
          type: data.type,
        };

        setMessages((prev) => [...prev, chatMsg]);
      } catch {
        // Ignore parse errors
      }
    };

    es.onerror = () => {
      setConnected(false);
    };

    return () => {
      es.close();
      eventSourceRef.current = null;
    };
  }, [projectId, isScanning]);

  // Auto-scroll on new messages
  useEffect(() => {
    if (scrollRef.current) {
      const el = scrollRef.current;
      el.scrollTop = el.scrollHeight;
    }
  }, [messages]);

  const getBubbleStyle = (type: string) => {
    switch (type) {
      case "error":
        return "border-red-500/30 bg-red-500/5";
      case "success":
        return "border-green-500/30 bg-green-500/5";
      case "warning":
        return "border-yellow-500/30 bg-yellow-500/5";
      default:
        return "border-border/40 bg-background/50";
    }
  };

  return (
    <Card className="border-border/50 bg-card/50">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-purple-400" />
            Live Agent Communication
          </CardTitle>
          {connected && (
            <Badge
              variant="outline"
              className="text-[10px] text-green-400 border-green-500/30 bg-green-500/10 gap-1"
            >
              <Radio className="h-2.5 w-2.5 animate-pulse" />
              Live
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div
          ref={scrollRef}
          className="h-[500px] overflow-y-auto px-4 py-3 space-y-3"
        >
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              <div className="text-center">
                <Bot className="h-10 w-10 mx-auto mb-3 opacity-30" />
                <p className="text-sm">
                  {isScanning
                    ? "Waiting for agent messages..."
                    : "Start a scan to see agents communicate"}
                </p>
              </div>
            </div>
          )}

          <AnimatePresence mode="popLayout">
            {messages.map((msg) => {
              const config = getAgentConfig(msg.agent);
              const Icon = config.icon;

              return (
                <motion.div
                  key={msg.id}
                  layout
                  initial={{ opacity: 0, y: 12, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.25 }}
                  className={`flex gap-3 rounded-lg border p-3 ${getBubbleStyle(msg.message_type)}`}
                >
                  {/* Agent avatar */}
                  <div
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${config.bgColor}`}
                  >
                    <Icon className={`h-4 w-4 ${config.color}`} />
                  </div>

                  {/* Message content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className={`text-xs font-semibold ${config.color}`}>
                        {config.label}
                      </span>
                      <span className="text-[10px] text-muted-foreground/50">
                        {new Date(msg.timestamp * 1000).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm text-foreground/80 leading-relaxed">
                      {msg.message}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </CardContent>
    </Card>
  );
}
