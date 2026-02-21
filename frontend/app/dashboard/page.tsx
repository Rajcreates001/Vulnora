"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { UploadPanel } from "@/components/upload-panel";
import { ScanProgress } from "@/components/scan-progress";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useVulnoraStore } from "@/store/vulnora-store";
import { getProjects } from "@/lib/api";
import {
  FolderOpen,
  Shield,
  Clock,
  ArrowRight,
  AlertTriangle,
} from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const { projects, setProjects, currentProject, scanStatus } =
    useVulnoraStore();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const data = await getProjects();
        setProjects(data.projects);
      } catch (e) {
        console.error("Failed to load projects", e);
      } finally {
        setLoading(false);
      }
    })();
  }, [setProjects]);

  const STATUS_BADGE: Record<string, string> = {
    completed: "bg-green-500/20 text-green-400 border-green-500/30",
    scanning: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    failed: "bg-red-500/20 text-red-400 border-red-500/30",
    pending: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    uploaded: "bg-muted text-muted-foreground border-border",
  };

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <h1 className="text-3xl font-bold mb-1">Dashboard</h1>
        <p className="text-muted-foreground mb-8">
          Upload a codebase and launch an autonomous security scan.
        </p>
      </motion.div>

      {/* Upload + Scan */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
        >
          <UploadPanel />
        </motion.div>

        {currentProject && scanStatus && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2 }}
          >
            <ScanProgress
              projectId={currentProject.id}
              scanStatus={scanStatus}
            />
          </motion.div>
        )}
      </div>

      {/* Projects List */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.3 }}
      >
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <FolderOpen className="h-5 w-5 text-indigo-400" />
          Recent Projects
        </h2>

        {loading ? (
          <div className="text-muted-foreground text-sm animate-pulse">
            Loading projects…
          </div>
        ) : projects.length === 0 ? (
          <Card className="border-border/50 bg-card/30">
            <CardContent className="flex flex-col items-center justify-center py-16 text-muted-foreground">
              <Shield className="h-10 w-10 mb-3 opacity-30" />
              <p className="text-sm">No projects yet. Upload a codebase to begin.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {projects.map((project, i) => (
              <motion.div
                key={project.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.05 * i }}
              >
                <Card className="border-border/50 bg-card/50 hover:bg-card/80 transition-colors">
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base truncate">
                        {project.name}
                      </CardTitle>
                      <Badge
                        variant="outline"
                        className={`text-[10px] ${STATUS_BADGE[project.scan_status] || STATUS_BADGE.uploaded}`}
                      >
                        {project.scan_status}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground mb-3">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {new Date(project.created_at).toLocaleDateString()}
                      </span>
                      {project.vulnerability_count != null &&
                        project.vulnerability_count > 0 && (
                          <span className="flex items-center gap-1 text-orange-400">
                            <AlertTriangle className="h-3 w-3" />
                            {project.vulnerability_count} vulns
                          </span>
                        )}
                    </div>
                    <Link href={`/results/${project.id}`}>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="w-full gap-1 text-xs"
                      >
                        View Results
                        <ArrowRight className="h-3.5 w-3.5" />
                      </Button>
                    </Link>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        )}
      </motion.div>
    </div>
  );
}
