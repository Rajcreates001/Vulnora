"use client";

import { useEffect, useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  FolderTree,
  Folder,
  FolderOpen,
  FileCode2,
  ChevronRight,
  ChevronDown,
  AlertTriangle,
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  Loader2,
  Eye,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { getProject } from "@/lib/api";

// ─── Types ──────────────────────────────

interface FileInfo {
  id: string;
  file_path: string;
  language: string;
  size: number;
}

interface TreeNode {
  name: string;
  path: string;
  type: "file" | "folder";
  language?: string;
  children: TreeNode[];
  vulnCount: number;
  maxSeverity: string;
  vulns: VulnRef[];
}

interface VulnRef {
  title: string;
  severity: string;
  line_start: number;
  cwe_id?: string;
}

interface FileStructureTreeProps {
  projectId: string;
  vulnerabilities: any[];
}

// ─── Build Tree ──────────────────────────

function buildTree(files: FileInfo[], vulnMap: Map<string, VulnRef[]>): TreeNode {
  const root: TreeNode = {
    name: "root",
    path: "",
    type: "folder",
    children: [],
    vulnCount: 0,
    maxSeverity: "none",
    vulns: [],
  };

  for (const file of files) {
    const parts = file.file_path.split("/");
    let current = root;

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      const isFile = i === parts.length - 1;
      const currentPath = parts.slice(0, i + 1).join("/");

      let existing = current.children.find((c) => c.name === part);

      if (!existing) {
        const fileVulns = isFile ? (vulnMap.get(file.file_path) || []) : [];
        existing = {
          name: part,
          path: currentPath,
          type: isFile ? "file" : "folder",
          language: isFile ? file.language : undefined,
          children: [],
          vulnCount: fileVulns.length,
          maxSeverity: getMaxSeverity(fileVulns),
          vulns: fileVulns,
        };
        current.children.push(existing);
      }

      current = existing;
    }
  }

  // Propagate vulnerability counts to parent folders
  propagateVulns(root);

  // Sort: folders first, then files, alphabetically
  sortTree(root);

  return root;
}

function propagateVulns(node: TreeNode): { count: number; maxSev: string } {
  if (node.type === "file") {
    return { count: node.vulnCount, maxSev: node.maxSeverity };
  }

  let totalCount = 0;
  let maxSev = "none";
  const sevOrder = ["none", "Low", "Medium", "High", "Critical"];

  for (const child of node.children) {
    const { count, maxSev: childSev } = propagateVulns(child);
    totalCount += count;
    if (sevOrder.indexOf(childSev) > sevOrder.indexOf(maxSev)) {
      maxSev = childSev;
    }
  }

  node.vulnCount = totalCount;
  node.maxSeverity = maxSev;
  return { count: totalCount, maxSev };
}

function sortTree(node: TreeNode) {
  node.children.sort((a, b) => {
    if (a.type !== b.type) return a.type === "folder" ? -1 : 1;
    return a.name.localeCompare(b.name);
  });
  for (const child of node.children) sortTree(child);
}

function getMaxSeverity(vulns: VulnRef[]): string {
  const sevOrder = ["none", "Low", "Medium", "High", "Critical"];
  let max = "none";
  for (const v of vulns) {
    if (sevOrder.indexOf(v.severity) > sevOrder.indexOf(max)) {
      max = v.severity;
    }
  }
  return max;
}

// ─── Severity Colors ──────────────────────

const SEV_CONFIG: Record<string, { color: string; bgColor: string; icon: any; label: string }> = {
  Critical: { color: "text-red-400", bgColor: "bg-red-500/10 border-red-500/30", icon: ShieldX, label: "Critical" },
  High: { color: "text-orange-400", bgColor: "bg-orange-500/10 border-orange-500/30", icon: ShieldAlert, label: "High" },
  Medium: { color: "text-yellow-400", bgColor: "bg-yellow-500/10 border-yellow-500/30", icon: AlertTriangle, label: "Medium" },
  Low: { color: "text-blue-400", bgColor: "bg-blue-500/10 border-blue-500/30", icon: ShieldCheck, label: "Low" },
  none: { color: "text-green-400", bgColor: "bg-green-500/10 border-green-500/30", icon: ShieldCheck, label: "Clean" },
};

const LANG_COLORS: Record<string, string> = {
  python: "text-yellow-400",
  javascript: "text-yellow-300",
  typescript: "text-blue-400",
  java: "text-orange-400",
  go: "text-cyan-400",
  rust: "text-orange-500",
  html: "text-red-400",
  css: "text-blue-300",
  sql: "text-green-400",
  json: "text-gray-400",
  yaml: "text-pink-400",
};

// ─── Tree Node Component ──────────────────

function TreeNodeItem({ node, depth = 0, expandedByDefault = false }: { node: TreeNode; depth?: number; expandedByDefault?: boolean }) {
  const [expanded, setExpanded] = useState(expandedByDefault || (depth < 1));
  const [showVulns, setShowVulns] = useState(false);
  const isFolder = node.type === "folder";
  const sevConfig = SEV_CONFIG[node.maxSeverity] || SEV_CONFIG.none;
  const SevIcon = sevConfig.icon;

  return (
    <div>
      <div
        onClick={() => {
          if (isFolder) setExpanded(!expanded);
          else if (node.vulns.length > 0) setShowVulns(!showVulns);
        }}
        className={cn(
          "flex items-center gap-2 py-1.5 px-2 rounded-md cursor-pointer transition-all duration-150 group",
          "hover:bg-accent/50",
          node.vulnCount > 0 && "hover:bg-red-500/5"
        )}
        style={{ paddingLeft: `${depth * 20 + 8}px` }}
      >
        {/* Expand Icon */}
        {isFolder ? (
          <span className="w-4 h-4 flex items-center justify-center text-muted-foreground">
            {expanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
          </span>
        ) : (
          <span className="w-4" />
        )}

        {/* File/Folder Icon */}
        {isFolder ? (
          expanded ? (
            <FolderOpen className="h-4 w-4 text-blue-400 shrink-0" />
          ) : (
            <Folder className="h-4 w-4 text-blue-400/70 shrink-0" />
          )
        ) : (
          <FileCode2 className={cn("h-4 w-4 shrink-0", LANG_COLORS[node.language || ""] || "text-muted-foreground")} />
        )}

        {/* Name */}
        <span className={cn("text-sm truncate flex-1", isFolder ? "font-medium" : "text-muted-foreground group-hover:text-foreground")}>
          {node.name}
        </span>

        {/* Vulnerability Indicator */}
        {node.vulnCount > 0 && (
          <div className="flex items-center gap-1.5 shrink-0">
            <SevIcon className={cn("h-3.5 w-3.5", sevConfig.color)} />
            <Badge variant="outline" className={cn("text-[10px] px-1.5 py-0", sevConfig.bgColor, sevConfig.color)}>
              {node.vulnCount} {node.vulnCount === 1 ? "issue" : "issues"}
            </Badge>
          </div>
        )}
        {node.type === "file" && node.vulnCount === 0 && (
          <ShieldCheck className="h-3.5 w-3.5 text-green-500/50 shrink-0" />
        )}
      </div>

      {/* Vulnerability Details for Files */}
      <AnimatePresence>
        {showVulns && node.vulns.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="ml-8 pl-4 border-l-2 border-border/50 space-y-1 py-1" style={{ marginLeft: `${depth * 20 + 32}px` }}>
              {node.vulns.map((v, i) => {
                const vSev = SEV_CONFIG[v.severity] || SEV_CONFIG.none;
                return (
                  <div key={i} className={cn("rounded px-2.5 py-1.5 text-xs border", vSev.bgColor)}>
                    <div className="flex items-center gap-2">
                      <AlertTriangle className={cn("h-3 w-3 shrink-0", vSev.color)} />
                      <span className={cn("font-medium", vSev.color)}>{v.severity}</span>
                      <span className="text-muted-foreground truncate">{v.title}</span>
                      {v.cwe_id && <span className="text-muted-foreground/70 font-mono">{v.cwe_id}</span>}
                      <span className="text-muted-foreground/50 ml-auto">L{v.line_start}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Children */}
      <AnimatePresence>
        {isFolder && expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.15 }}
          >
            {node.children.map((child) => (
              <TreeNodeItem key={child.path} node={child} depth={depth + 1} />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ─── Main Component ──────────────────────

export function FileStructureTree({ projectId, vulnerabilities }: FileStructureTreeProps) {
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const project = await getProject(projectId);
        setFiles(project.files || []);
      } catch (e) {
        console.error("Failed to load project files", e);
      } finally {
        setLoading(false);
      }
    })();
  }, [projectId]);

  // Build vulnerability map: file_path → VulnRef[]
  const vulnMap = useMemo(() => {
    const map = new Map<string, VulnRef[]>();
    for (const v of vulnerabilities) {
      const fp = v.file_path || "";
      if (!map.has(fp)) map.set(fp, []);
      map.get(fp)!.push({
        title: v.title,
        severity: v.severity,
        line_start: v.line_start || 0,
        cwe_id: v.cwe_id,
      });
    }
    return map;
  }, [vulnerabilities]);

  const tree = useMemo(() => buildTree(files, vulnMap), [files, vulnMap]);

  // Summary stats
  const totalFiles = files.length;
  const affectedFiles = new Set(vulnerabilities.map((v: any) => v.file_path)).size;
  const cleanFiles = totalFiles - affectedFiles;

  if (loading) {
    return (
      <Card className="border-border/50 bg-card/50">
        <CardContent className="flex items-center justify-center py-16 text-muted-foreground">
          <Loader2 className="h-6 w-6 animate-spin mr-2" />
          Loading file structure...
        </CardContent>
      </Card>
    );
  }

  if (files.length === 0) {
    return (
      <Card className="border-border/50 bg-card/50">
        <CardContent className="flex flex-col items-center justify-center py-16 text-muted-foreground">
          <FolderTree className="h-10 w-10 mb-3 opacity-30" />
          <p className="text-sm">No files found in project</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card className="border-border/50 bg-card/50">
          <CardContent className="py-3 px-4">
            <div className="text-2xl font-bold">{totalFiles}</div>
            <div className="text-xs text-muted-foreground">Total Files</div>
          </CardContent>
        </Card>
        <Card className="border-border/50 bg-red-500/5 border-red-500/20">
          <CardContent className="py-3 px-4">
            <div className="text-2xl font-bold text-red-400">{affectedFiles}</div>
            <div className="text-xs text-red-400/70">Affected Files</div>
          </CardContent>
        </Card>
        <Card className="border-border/50 bg-green-500/5 border-green-500/20">
          <CardContent className="py-3 px-4">
            <div className="text-2xl font-bold text-green-400">{cleanFiles}</div>
            <div className="text-xs text-green-400/70">Clean Files</div>
          </CardContent>
        </Card>
        <Card className="border-border/50 bg-card/50">
          <CardContent className="py-3 px-4">
            <div className="text-2xl font-bold text-orange-400">{vulnerabilities.length}</div>
            <div className="text-xs text-orange-400/70">Total Issues</div>
          </CardContent>
        </Card>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
        <span className="flex items-center gap-1"><ShieldX className="h-3 w-3 text-red-400" /> Critical</span>
        <span className="flex items-center gap-1"><ShieldAlert className="h-3 w-3 text-orange-400" /> High</span>
        <span className="flex items-center gap-1"><AlertTriangle className="h-3 w-3 text-yellow-400" /> Medium</span>
        <span className="flex items-center gap-1"><ShieldCheck className="h-3 w-3 text-blue-400" /> Low</span>
        <span className="flex items-center gap-1"><ShieldCheck className="h-3 w-3 text-green-400" /> Clean</span>
      </div>

      {/* Tree */}
      <Card className="border-border/50 bg-card/50">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <FolderTree className="h-5 w-5 text-blue-400" />
            Project File Structure
          </CardTitle>
        </CardHeader>
        <CardContent className="p-2">
          <ScrollArea className="h-[600px]">
            <div className="pr-4">
              {tree.children.map((child) => (
                <TreeNodeItem key={child.path} node={child} depth={0} expandedByDefault />
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
