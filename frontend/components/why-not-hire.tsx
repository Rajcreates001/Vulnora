"use client";

import { motion } from "framer-motion";
import { XCircle, ArrowRight, BookOpen, Calendar, Lightbulb } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { WhyNotHire as WhyNotHireType, ImprovementRoadmap } from "@/lib/api";

interface WhyNotHirePanelProps {
  data: WhyNotHireType | null;
  roadmap: ImprovementRoadmap | null;
  decision: string;
}

export function WhyNotHirePanel({ data, roadmap, decision }: WhyNotHirePanelProps) {
  if (decision.toLowerCase() === "hire" || !data) {
    return (
      <Card className="glass-card">
        <CardContent className="py-12 text-center">
          <Lightbulb className="w-10 h-10 text-emerald-400 mx-auto mb-3 opacity-60" />
          <p className="text-emerald-400 font-medium">Candidate Approved</p>
          <p className="text-muted-foreground text-sm mt-1">
            No rejection explanation needed.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Why Not Hire */}
      <Card className="glass-card border-red-500/20">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2 text-red-400">
            <XCircle className="w-4 h-4" />
            Why Not Hire — Structured Explanation
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Major Weaknesses */}
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              Major Weaknesses
            </p>
            <div className="space-y-1.5">
              {data.major_weaknesses.map((w, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -5 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="flex items-start gap-2 text-sm"
                >
                  <span className="text-red-400 mt-0.5">&#x2022;</span>
                  <span className="text-muted-foreground">{w}</span>
                </motion.div>
              ))}
            </div>
          </div>

          <Separator className="bg-border/30" />

          {/* Evidence */}
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              Supporting Evidence
            </p>
            <div className="space-y-1.5">
              {data.evidence.map((e, i) => (
                <div key={i} className="flex items-start gap-2 text-sm">
                  <ArrowRight className="w-3 h-3 mt-1 text-amber-400 shrink-0" />
                  <span className="text-muted-foreground">{e}</span>
                </div>
              ))}
            </div>
          </div>

          <Separator className="bg-border/30" />

          {/* Risk Justification */}
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              Risk Justification
            </p>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {data.risk_justification}
            </p>
          </div>

          <Separator className="bg-border/30" />

          {/* Improvement Suggestions */}
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              Improvement Suggestions
            </p>
            <div className="space-y-1.5">
              {data.improvement_suggestions.map((s, i) => (
                <div key={i} className="flex items-start gap-2 text-sm">
                  <Lightbulb className="w-3 h-3 mt-1 text-cyan-400 shrink-0" />
                  <span className="text-muted-foreground">{s}</span>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 30-Day Improvement Roadmap */}
      {roadmap && (
        <Card className="glass-card border-cyan-500/20">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2 text-cyan-400">
              <Calendar className="w-4 h-4" />
              30-Day Improvement Roadmap
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              {[
                { label: "Week 1", tasks: roadmap.week_1 },
                { label: "Week 2", tasks: roadmap.week_2 },
                { label: "Week 3", tasks: roadmap.week_3 },
                { label: "Week 4", tasks: roadmap.week_4 },
              ].map((week, wi) => (
                <motion.div
                  key={week.label}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: wi * 0.15 }}
                  className="glass-card p-3"
                >
                  <p className="text-xs font-semibold text-primary mb-2">{week.label}</p>
                  <div className="space-y-1">
                    {week.tasks.map((task, i) => (
                      <p key={i} className="text-xs text-muted-foreground">
                        • {task}
                      </p>
                    ))}
                  </div>
                </motion.div>
              ))}
            </div>

            {roadmap.resources.length > 0 && (
              <div className="mt-4">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                  Recommended Resources
                </p>
                <div className="flex flex-wrap gap-2">
                  {roadmap.resources.map((r, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs bg-secondary text-muted-foreground"
                    >
                      <BookOpen className="w-3 h-3" />
                      {r}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
