"use client";

import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Code2 } from "lucide-react";

interface CodeViewerProps {
  code: string;
  language?: string;
  vulnerableLine?: number;
  title?: string;
  severity?: string;
}

const SEVERITY_BORDER: Record<string, string> = {
  critical: "border-red-500/60",
  high: "border-orange-500/60",
  medium: "border-yellow-500/60",
  low: "border-green-500/60",
};

const SEVERITY_HIGHLIGHT: Record<string, string> = {
  critical: "bg-red-500/15 border-l-2 border-l-red-500",
  high: "bg-orange-500/15 border-l-2 border-l-orange-500",
  medium: "bg-yellow-500/15 border-l-2 border-l-yellow-500",
  low: "bg-green-500/15 border-l-2 border-l-green-500",
};

export function CodeViewer({
  code,
  language = "text",
  vulnerableLine,
  title,
  severity = "medium",
}: CodeViewerProps) {
  const lines = useMemo(() => code.split("\n"), [code]);

  const borderColor = SEVERITY_BORDER[severity.toLowerCase()] || "border-border/50";
  const highlightClass = SEVERITY_HIGHLIGHT[severity.toLowerCase()] || "";

  return (
    <Card className={`${borderColor} bg-card/50`}>
      {title && (
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <Code2 className="h-4 w-4 text-indigo-400" />
            {title}
            {language !== "text" && (
              <Badge variant="outline" className="text-[10px] ml-auto">
                {language}
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
      )}
      <CardContent className={title ? "pt-0" : "p-0"}>
        <div className="rounded-lg bg-[#0d1117] overflow-x-auto">
          <table className="w-full text-[12px] font-mono leading-5">
            <tbody>
              {lines.map((line, i) => {
                const lineNum = i + 1;
                const isVulnerable = vulnerableLine === lineNum;
                return (
                  <tr
                    key={i}
                    className={
                      isVulnerable
                        ? highlightClass
                        : "hover:bg-white/[0.03]"
                    }
                  >
                    <td className="select-none text-right pr-4 pl-3 py-0 text-muted-foreground/40 w-[1%] whitespace-nowrap">
                      {lineNum}
                    </td>
                    <td className="pr-4 py-0 whitespace-pre text-muted-foreground">
                      {line || " "}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
