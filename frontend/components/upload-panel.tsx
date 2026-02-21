"use client";

import { useCallback, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, Link as LinkIcon, FileArchive, Loader2, CheckCircle2, FolderTree, ArrowRight, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { uploadRepo, startScan } from "@/lib/api";
import { useVulnoraStore } from "@/store/vulnora-store";

export function UploadPanel() {
  const router = useRouter();
  const [mode, setMode] = useState<"zip" | "github">("zip");
  const [repoUrl, setRepoUrl] = useState("");
  const [projectName, setProjectName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [startingScan, setStartingScan] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { isUploading, setIsUploading } = useVulnoraStore();

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile?.name.endsWith(".zip")) {
      setFile(droppedFile);
      if (!projectName) setProjectName(droppedFile.name.replace(".zip", ""));
    }
  }, [projectName]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) {
      setFile(selected);
      if (!projectName) setProjectName(selected.name.replace(".zip", ""));
    }
  };

  const handleUpload = async () => {
    if (!projectName) return;
    setIsUploading(true);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append("project_name", projectName);

      if (mode === "zip" && file) {
        formData.append("file", file);
      } else if (mode === "github" && repoUrl) {
        formData.append("repo_url", repoUrl);
      } else {
        setIsUploading(false);
        return;
      }

      const result = await uploadRepo(formData);
      setUploadResult(result);
    } catch (error: any) {
      setUploadResult({ error: error.message });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Upload className="h-5 w-5 text-blue-400" />
          Upload Repository
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Mode Toggle */}
        <div className="flex gap-2">
          <Button
            variant={mode === "zip" ? "default" : "outline"}
            size="sm"
            onClick={() => setMode("zip")}
            className="flex-1"
          >
            <FileArchive className="mr-2 h-4 w-4" />
            ZIP File
          </Button>
          <Button
            variant={mode === "github" ? "default" : "outline"}
            size="sm"
            onClick={() => setMode("github")}
            className="flex-1"
          >
            <LinkIcon className="mr-2 h-4 w-4" />
            GitHub URL
          </Button>
        </div>

        {/* Project Name */}
        <input
          type="text"
          placeholder="Project name"
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />

        <AnimatePresence mode="wait">
          {mode === "zip" ? (
            <motion.div
              key="zip"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              {/* Drop Zone */}
              <div
                onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
                onDragLeave={() => setDragActive(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`relative flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-all duration-200 ${
                  dragActive
                    ? "border-blue-500 bg-blue-500/5"
                    : "border-border hover:border-muted-foreground/50"
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".zip"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                <FileArchive className={`h-10 w-10 mb-3 ${file ? "text-blue-400" : "text-muted-foreground"}`} />
                {file ? (
                  <p className="text-sm text-blue-400 font-medium">{file.name}</p>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Drop ZIP file here or click to browse
                  </p>
                )}
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="github"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              <input
                type="url"
                placeholder="https://github.com/user/repo"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Upload Button */}
        <Button
          onClick={handleUpload}
          disabled={isUploading || !projectName || (mode === "zip" ? !file : !repoUrl)}
          className="w-full bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white"
        >
          {isUploading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <Upload className="mr-2 h-4 w-4" />
              Upload & Analyze
            </>
          )}
        </Button>

        {/* Upload Result */}
        <AnimatePresence>
          {uploadResult && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
            >
              {uploadResult.error ? (
                <div className="rounded-md border border-red-500/20 bg-red-500/5 p-3 text-sm text-red-400">
                  {uploadResult.error}
                </div>
              ) : (
                <div className="rounded-md border border-green-500/20 bg-green-500/5 p-4 space-y-3">
                  <div className="flex items-center gap-2 text-sm text-green-400 font-medium">
                    <CheckCircle2 className="h-4 w-4" />
                    Project uploaded successfully
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <FolderTree className="h-3 w-3" />
                    {uploadResult.file_count} files detected
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2 pt-1">
                    <Button
                      size="sm"
                      variant="outline"
                      className="flex-1 gap-1"
                      onClick={() => router.push(`/results/${uploadResult.project_id}`)}
                    >
                      <ArrowRight className="h-3.5 w-3.5" />
                      View Project
                    </Button>
                    <Button
                      size="sm"
                      className="flex-1 gap-1 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white"
                      disabled={startingScan}
                      onClick={async () => {
                        setStartingScan(true);
                        try {
                          await startScan(uploadResult.project_id, true);
                          router.push(`/results/${uploadResult.project_id}`);
                        } catch (e: any) {
                          console.error("Failed to start scan", e);
                          // Still navigate — user can start scan from results page
                          router.push(`/results/${uploadResult.project_id}`);
                        }
                        // Don't reset startingScan — we're navigating away
                      }}
                    >
                      {startingScan ? (
                        <>
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          Starting Scan...
                        </>
                      ) : (
                        <>
                          <Play className="h-3.5 w-3.5" />
                          Scan Now
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </CardContent>
    </Card>
  );
}
