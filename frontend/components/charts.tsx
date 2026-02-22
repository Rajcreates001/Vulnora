"use client";

import { motion } from "framer-motion";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface SkillRadarProps {
  data: {
    technical: number;
    behavior: number;
    domain: number;
    communication: number;
    risk: number;
    learning: number;
  };
}

export function SkillRadarChart({ data }: SkillRadarProps) {
  const chartData = [
    { subject: "Technical", score: data.technical, fullMark: 100 },
    { subject: "Behavioral", score: data.behavior, fullMark: 100 },
    { subject: "Domain", score: data.domain, fullMark: 100 },
    { subject: "Communication", score: data.communication, fullMark: 100 },
    { subject: "Risk Safety", score: data.risk, fullMark: 100 },
    { subject: "Learning", score: data.learning, fullMark: 100 },
  ];

  return (
    <Card className="glass-card">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Skill Radar</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={chartData}>
              <PolarGrid stroke="hsl(217 33% 20%)" />
              <PolarAngleAxis
                dataKey="subject"
                tick={{ fill: "hsl(215 20% 55%)", fontSize: 11 }}
              />
              <PolarRadiusAxis
                angle={90}
                domain={[0, 100]}
                tick={{ fill: "hsl(215 20% 45%)", fontSize: 9 }}
              />
              <Radar
                name="Candidate"
                dataKey="score"
                stroke="hsl(199 89% 48%)"
                fill="hsl(199 89% 48%)"
                fillOpacity={0.2}
                strokeWidth={2}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

interface ScoreBarProps {
  scores: Array<{ name: string; score: number }>;
}

export function ScoreBarChart({ scores }: ScoreBarProps) {
  const getColor = (score: number) => {
    if (score >= 80) return "#10b981";
    if (score >= 60) return "#f59e0b";
    if (score >= 40) return "#f97316";
    return "#ef4444";
  };

  return (
    <Card className="glass-card">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Score Breakdown</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={scores} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(217 33% 15%)" />
              <XAxis
                type="number"
                domain={[0, 100]}
                tick={{ fill: "hsl(215 20% 55%)", fontSize: 11 }}
              />
              <YAxis
                dataKey="name"
                type="category"
                tick={{ fill: "hsl(215 20% 55%)", fontSize: 11 }}
                width={100}
              />
              <Tooltip
                contentStyle={{
                  background: "hsl(222 47% 8%)",
                  border: "1px solid hsl(217 33% 17%)",
                  borderRadius: "8px",
                  color: "hsl(210 40% 96%)",
                }}
              />
              <Bar dataKey="score" radius={[0, 4, 4, 0]} barSize={20}>
                {scores.map((entry, index) => (
                  <Cell key={index} fill={getColor(entry.score)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

interface ConfidenceMeterProps {
  confidence: number;
  decision: string;
}

export function ConfidenceMeter({ confidence, decision }: ConfidenceMeterProps) {
  const getDecisionColor = (d: string) => {
    switch (d.toLowerCase()) {
      case "hire": return "#10b981";
      case "no hire":
      case "no_hire": return "#ef4444";
      default: return "#f59e0b";
    }
  };

  const color = getDecisionColor(decision);
  const circumference = 2 * Math.PI * 58;
  const dashOffset = circumference - (confidence / 100) * circumference;

  return (
    <Card className="glass-card">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Hiring Confidence</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center">
        <div className="relative w-36 h-36">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 128 128">
            <circle
              cx="64"
              cy="64"
              r="58"
              fill="none"
              stroke="hsl(217 33% 15%)"
              strokeWidth="8"
            />
            <motion.circle
              cx="64"
              cy="64"
              r="58"
              fill="none"
              stroke={color}
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={circumference}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset: dashOffset }}
              transition={{ duration: 1.5, ease: "easeOut" }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <motion.span
              className="text-3xl font-bold"
              style={{ color }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
            >
              {confidence}%
            </motion.span>
          </div>
        </div>
        <motion.div
          className="mt-3 px-3 py-1 rounded-full text-sm font-semibold border"
          style={{
            color,
            borderColor: `${color}40`,
            backgroundColor: `${color}15`,
          }}
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
        >
          {decision}
        </motion.div>
      </CardContent>
    </Card>
  );
}

interface RiskGaugeProps {
  riskScore: number;
  attritionRisk: number;
}

export function RiskGauge({ riskScore, attritionRisk }: RiskGaugeProps) {
  const getRiskColor = (score: number) => {
    if (score <= 30) return "#10b981";
    if (score <= 60) return "#f59e0b";
    return "#ef4444";
  };

  return (
    <Card className="glass-card">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Risk Assessment</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-muted-foreground">Hiring Risk</span>
            <span style={{ color: getRiskColor(riskScore) }}>{riskScore}%</span>
          </div>
          <div className="h-2 bg-secondary rounded-full overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{ backgroundColor: getRiskColor(riskScore) }}
              initial={{ width: 0 }}
              animate={{ width: `${riskScore}%` }}
              transition={{ duration: 1, ease: "easeOut" }}
            />
          </div>
        </div>
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-muted-foreground">Attrition Risk</span>
            <span style={{ color: getRiskColor(attritionRisk) }}>{attritionRisk}%</span>
          </div>
          <div className="h-2 bg-secondary rounded-full overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{ backgroundColor: getRiskColor(attritionRisk) }}
              initial={{ width: 0 }}
              animate={{ width: `${attritionRisk}%` }}
              transition={{ duration: 1, delay: 0.2, ease: "easeOut" }}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface AgentAgreementProps {
  opinions: Array<{
    agent_name: string;
    decision: string;
    confidence: number;
  }>;
}

export function AgentAgreementChart({ opinions }: AgentAgreementProps) {
  const data = opinions.map((o) => ({
    name: o.agent_name.split(" ")[0],
    confidence: o.confidence,
    decision: o.decision,
  }));

  const getDecisionColor = (d: string) => {
    switch (d?.toLowerCase()) {
      case "hire": return "#10b981";
      case "no_hire":
      case "no hire": return "#ef4444";
      default: return "#f59e0b";
    }
  };

  return (
    <Card className="glass-card">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Agent Agreement</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(217 33% 15%)" />
              <XAxis
                dataKey="name"
                tick={{ fill: "hsl(215 20% 55%)", fontSize: 10 }}
                angle={-15}
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fill: "hsl(215 20% 55%)", fontSize: 11 }}
              />
              <Tooltip
                contentStyle={{
                  background: "hsl(222 47% 8%)",
                  border: "1px solid hsl(217 33% 17%)",
                  borderRadius: "8px",
                  color: "hsl(210 40% 96%)",
                }}
              />
              <Bar dataKey="confidence" radius={[4, 4, 0, 0]}>
                {data.map((entry, index) => (
                  <Cell key={index} fill={getDecisionColor(entry.decision)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
