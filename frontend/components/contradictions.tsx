"use client";

import { motion } from "framer-motion";
import { AlertTriangle, XCircle, AlertOctagon, Info } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getSeverityColor } from "@/lib/utils";
import type { Contradiction } from "@/lib/api";

interface ContradictionPanelProps {
  contradictions: Contradiction[];
}

export function ContradictionPanel({ contradictions }: ContradictionPanelProps) {
  if (!contradictions || contradictions.length === 0) {
    return (
      <Card className="glass-card">
        <CardContent className="py-12 text-center">
          <AlertTriangle className="w-10 h-10 text-muted-foreground mx-auto mb-3 opacity-40" />
          <p className="text-muted-foreground">No contradictions detected.</p>
        </CardContent>
      </Card>
    );
  }

  const severityIcons: Record<string, typeof AlertTriangle> = {
    critical: XCircle,
    high: AlertOctagon,
    medium: AlertTriangle,
    low: Info,
  };

  return (
    <Card className="glass-card">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          Contradictions Detected
          <Badge variant="destructive" className="ml-auto">
            {contradictions.length} found
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {contradictions.map((c, i) => {
          const SeverityIcon = severityIcons[c.severity] || AlertTriangle;
          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="glass-card p-4 space-y-2"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-2">
                  <SeverityIcon
                    className={`w-4 h-4 mt-0.5 ${
                      c.severity === "critical"
                        ? "text-red-400"
                        : c.severity === "high"
                        ? "text-orange-400"
                        : c.severity === "medium"
                        ? "text-amber-400"
                        : "text-blue-400"
                    }`}
                  />
                  <div>
                    <p className="text-sm font-medium">Claim: {c.claim}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Evidence: {c.evidence}
                    </p>
                  </div>
                </div>
                <Badge className={getSeverityColor(c.severity)}>
                  {c.severity}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground pl-6">{c.explanation}</p>
            </motion.div>
          );
        })}
      </CardContent>
    </Card>
  );
}
