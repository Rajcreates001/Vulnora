"use client";

import { motion } from "framer-motion";
import { Target, ArrowUpRight, Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { getSeverityColor } from "@/lib/utils";
import type { SkillGap } from "@/lib/api";

interface SkillGapPanelProps {
  gaps: SkillGap[];
}

export function SkillGapPanel({ gaps }: SkillGapPanelProps) {
  if (!gaps || gaps.length === 0) {
    return (
      <Card className="glass-card">
        <CardContent className="py-12 text-center">
          <Target className="w-10 h-10 text-muted-foreground mx-auto mb-3 opacity-40" />
          <p className="text-muted-foreground">No skill gaps identified.</p>
        </CardContent>
      </Card>
    );
  }

  const levelToNum = (level: string): number => {
    switch (level.toLowerCase()) {
      case "expert": return 100;
      case "advanced": return 80;
      case "proficient":
      case "intermediate": return 60;
      case "beginner": return 30;
      case "none": return 0;
      default: return 40;
    }
  };

  return (
    <Card className="glass-card">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Target className="w-4 h-4 text-primary" />
          Skill Gap Analysis
          <Badge variant="outline" className="ml-auto">
            {gaps.length} gaps
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {gaps.map((gap, i) => {
          const currentPct = levelToNum(gap.current_level);
          const requiredPct = levelToNum(gap.required_level);

          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="glass-card p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">{gap.skill}</span>
                <Badge className={getSeverityColor(gap.gap_severity)}>
                  {gap.gap_severity}
                </Badge>
              </div>

              <div className="space-y-2">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-muted-foreground">Current: {gap.current_level}</span>
                    <span className="text-muted-foreground">Required: {gap.required_level}</span>
                  </div>
                  <div className="relative">
                    <Progress value={currentPct} className="h-2" />
                    <div
                      className="absolute top-0 h-2 border-r-2 border-dashed border-amber-400"
                      style={{ left: `${requiredPct}%` }}
                    />
                  </div>
                </div>

                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Clock className="w-3 h-3" />
                  Training estimate: {gap.training_estimate}
                </div>
              </div>
            </motion.div>
          );
        })}
      </CardContent>
    </Card>
  );
}
