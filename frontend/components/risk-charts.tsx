"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart3 } from "lucide-react";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "#ef4444",
  high: "#f97316",
  medium: "#eab308",
  low: "#22c55e",
  info: "#6366f1",
};

interface Vulnerability {
  id: string;
  severity: string;
  risk_score?: number;
  confidence?: number;
  exploitability?: number;
  impact?: number;
  vuln_type?: string;
  [key: string]: any;
}

interface RiskChartsProps {
  vulnerabilities: Vulnerability[];
}

export function RiskCharts({ vulnerabilities }: RiskChartsProps) {
  if (!vulnerabilities?.length) {
    return (
      <Card className="border-border/50 bg-card/50">
        <CardContent className="flex items-center justify-center py-16 text-muted-foreground">
          <div className="text-center">
            <BarChart3 className="h-10 w-10 mx-auto mb-3 opacity-30" />
            <p className="text-sm">No vulnerability data to chart</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Severity distribution
  const severityCounts = vulnerabilities.reduce(
    (acc, v) => {
      const key = (v.severity || "info").toLowerCase();
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  const severityData = ["critical", "high", "medium", "low", "info"]
    .filter((s) => severityCounts[s])
    .map((s) => ({
      name: s.charAt(0).toUpperCase() + s.slice(1),
      count: severityCounts[s] || 0,
      color: SEVERITY_COLORS[s],
    }));

  // Pie chart data
  const pieData = severityData.map((d) => ({
    name: d.name,
    value: d.count,
  }));

  // Avg risk metrics for radar chart
  const avgMetrics = {
    risk_score: 0,
    confidence: 0,
    exploitability: 0,
    impact: 0,
  };
  let count = 0;
  vulnerabilities.forEach((v) => {
    if (v.risk_score != null) {
      avgMetrics.risk_score += v.risk_score;
      avgMetrics.confidence += v.confidence || 0;
      avgMetrics.exploitability += v.exploitability || 0;
      avgMetrics.impact += v.impact || 0;
      count++;
    }
  });
  if (count > 0) {
    avgMetrics.risk_score /= count;
    avgMetrics.confidence /= count;
    avgMetrics.exploitability /= count;
    avgMetrics.impact /= count;
  }

  const radarData = [
    { metric: "Risk", value: Math.round(avgMetrics.risk_score) },
    { metric: "Confidence", value: Math.round(avgMetrics.confidence) },
    { metric: "Exploitability", value: Math.round(avgMetrics.exploitability) },
    { metric: "Impact", value: Math.round(avgMetrics.impact) },
  ];

  // Top vulns by risk_score
  const topVulns = [...vulnerabilities]
    .sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0))
    .slice(0, 8)
    .map((v) => ({
      name: (v.vuln_type || v.id || "").slice(0, 18),
      risk: v.risk_score || 0,
      fill: SEVERITY_COLORS[(v.severity || "info").toLowerCase()] || "#6366f1",
    }));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    return (
      <div className="bg-card border border-border rounded-lg px-3 py-2 shadow-lg text-xs">
        <p className="font-semibold text-foreground">{label}</p>
        {payload.map((entry: any, i: number) => (
          <p key={i} style={{ color: entry.color || entry.fill }}>
            {entry.name}: {entry.value}
          </p>
        ))}
      </div>
    );
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Severity Distribution Bar Chart */}
      <Card className="border-border/50 bg-card/50">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Severity Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={severityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} allowDecimals={false} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {severityData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Severity Pie Chart */}
      <Card className="border-border/50 bg-card/50">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Severity Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {pieData.map((entry, i) => (
                    <Cell
                      key={i}
                      fill={SEVERITY_COLORS[entry.name.toLowerCase()] || "#6366f1"}
                    />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  formatter={(value: string) => (
                    <span className="text-xs text-muted-foreground">{value}</span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Radar Chart */}
      <Card className="border-border/50 bg-card/50">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Average Risk Profile</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData} cx="50%" cy="50%" outerRadius={80}>
                <PolarGrid stroke="#1e293b" />
                <PolarAngleAxis
                  dataKey="metric"
                  tick={{ fill: "#94a3b8", fontSize: 11 }}
                />
                <PolarRadiusAxis
                  angle={30}
                  domain={[0, 100]}
                  tick={{ fill: "#64748b", fontSize: 9 }}
                />
                <Radar
                  name="Score"
                  dataKey="value"
                  stroke="#6366f1"
                  fill="#6366f1"
                  fillOpacity={0.3}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Top Risk Scores */}
      <Card className="border-border/50 bg-card/50">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Top Risk Scores</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topVulns} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis
                  type="number"
                  domain={[0, 100]}
                  tick={{ fill: "#94a3b8", fontSize: 11 }}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={110}
                  tick={{ fill: "#94a3b8", fontSize: 10 }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="risk" radius={[0, 4, 4, 0]}>
                  {topVulns.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
