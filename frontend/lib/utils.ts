import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatScore(score: number): string {
  return Math.round(score).toString();
}

export function getScoreColor(score: number): string {
  if (score >= 80) return "text-emerald-400";
  if (score >= 60) return "text-amber-400";
  if (score >= 40) return "text-orange-400";
  return "text-red-400";
}

export function getScoreBgColor(score: number): string {
  if (score >= 80) return "bg-emerald-500/20 border-emerald-500/30";
  if (score >= 60) return "bg-amber-500/20 border-amber-500/30";
  if (score >= 40) return "bg-orange-500/20 border-orange-500/30";
  return "bg-red-500/20 border-red-500/30";
}

export function getVerdictColor(decision: string): string {
  const d = (decision || "").toLowerCase();
  if (d.includes("strong hire")) return "text-emerald-400";
  if (d.includes("hire") && !d.includes("no") && !d.includes("not")) return "text-blue-400";
  if (d.includes("hold") || d.includes("conditional")) return "text-amber-400";
  if (d.includes("reject") || d.includes("no hire") || d.includes("not")) return "text-red-400";
  return "text-muted-foreground";
}

export function getVerdictBgColor(decision: string): string {
  const d = (decision || "").toLowerCase();
  if (d.includes("strong hire")) return "bg-emerald-500/15 border-emerald-500/30";
  if (d.includes("hire") && !d.includes("no") && !d.includes("not")) return "bg-blue-500/15 border-blue-500/30";
  if (d.includes("hold") || d.includes("conditional")) return "bg-amber-500/15 border-amber-500/30";
  if (d.includes("reject") || d.includes("no hire") || d.includes("not")) return "bg-red-500/15 border-red-500/30";
  return "bg-muted border-border";
}

export function getSeverityColor(severity: string): string {
  switch ((severity || "").toLowerCase()) {
    case "critical":
      return "text-red-400 bg-red-500/15";
    case "high":
      return "text-orange-400 bg-orange-500/15";
    case "medium":
      return "text-amber-400 bg-amber-500/15";
    case "low":
      return "text-blue-400 bg-blue-500/15";
    default:
      return "text-muted-foreground bg-muted";
  }
}

export function getSeverityDot(severity: string): string {
  switch ((severity || "").toLowerCase()) {
    case "critical":
      return "bg-red-500";
    case "high":
      return "bg-orange-500";
    case "medium":
      return "bg-amber-500";
    case "low":
      return "bg-blue-500";
    default:
      return "bg-muted-foreground";
  }
}
