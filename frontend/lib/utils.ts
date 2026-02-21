import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    Critical: "text-red-500 bg-red-500/10 border-red-500/20",
    High: "text-orange-500 bg-orange-500/10 border-orange-500/20",
    Medium: "text-yellow-500 bg-yellow-500/10 border-yellow-500/20",
    Low: "text-green-500 bg-green-500/10 border-green-500/20",
  };
  return colors[severity] || colors.Medium;
}

export function getSeverityDot(severity: string): string {
  const colors: Record<string, string> = {
    Critical: "bg-red-500",
    High: "bg-orange-500",
    Medium: "bg-yellow-500",
    Low: "bg-green-500",
  };
  return colors[severity] || colors.Medium;
}

export function getRiskGradient(score: number): string {
  if (score >= 80) return "from-red-600 to-red-400";
  if (score >= 60) return "from-orange-600 to-orange-400";
  if (score >= 40) return "from-yellow-600 to-yellow-400";
  return "from-green-600 to-green-400";
}
