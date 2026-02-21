"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Shield, Github, ArrowLeft, LayoutDashboard } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const isHome = pathname === "/";
  const isDashboard = pathname === "/dashboard";
  const showBack = !isHome;

  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="sticky top-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-xl"
    >
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <div className="flex items-center gap-4">
          {showBack && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.back()}
              className="text-muted-foreground hover:text-foreground -ml-2"
            >
              <ArrowLeft className="h-4 w-4 mr-1" />
              Back
            </Button>
          )}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="relative flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-cyan-500 shadow-lg shadow-blue-500/20 group-hover:shadow-blue-500/40 transition-shadow duration-300">
              <Shield className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold tracking-tight">
              Vuln<span className="text-blue-400">ora</span>
            </span>
          </Link>
        </div>

        <div className="flex items-center gap-4">
          <Link href="/dashboard">
            <Button
              variant={isDashboard ? "default" : "ghost"}
              size="sm"
              className="gap-1.5"
            >
              <LayoutDashboard className="h-4 w-4" />
              Dashboard
            </Button>
          </Link>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-muted-foreground hover:text-foreground transition-colors duration-200"
          >
            <Github className="h-5 w-5" />
          </a>
        </div>
      </div>
    </motion.nav>
  );
}
