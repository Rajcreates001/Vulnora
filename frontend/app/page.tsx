"use client";

import { motion } from "framer-motion";
import { Shield, Zap, GitBranch, FileSearch, Bot, ChevronRight } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

const FEATURES = [
  {
    icon: Bot,
    title: "8 AI Agents",
    desc: "Recon → Static Analysis → Vulnerability → Exploit → Patch → Risk → Debate → Report",
  },
  {
    icon: FileSearch,
    title: "Deep Code Analysis",
    desc: "Multi-language support with semantic understanding and pattern matching",
  },
  {
    icon: GitBranch,
    title: "Attack Path Mapping",
    desc: "Visual graph of exploitation pathways from entry point to impact",
  },
  {
    icon: Zap,
    title: "Auto Patch Generation",
    desc: "AI-generated secure code fixes with explanations for every vulnerability",
  },
];

export default function HomePage() {
  return (
    <div className="flex flex-col items-center justify-center px-6">
      {/* Hero */}
      <section className="flex flex-col items-center text-center pt-24 pb-16 max-w-3xl mx-auto">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        >
          <div className="relative mb-8">
            <div className="absolute inset-0 blur-3xl opacity-20 bg-indigo-500 rounded-full" />
            <Shield className="h-20 w-20 text-indigo-400 relative" />
          </div>
        </motion.div>

        <motion.h1
          className="text-5xl md:text-6xl font-bold tracking-tight bg-gradient-to-r from-indigo-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.15 }}
        >
          Vulnora
        </motion.h1>

        <motion.p
          className="text-lg md:text-xl text-muted-foreground mt-4 max-w-xl"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.25 }}
        >
          Autonomous Security Research Agent — AI-powered vulnerability
          discovery, exploit simulation, and patch generation for your codebase.
        </motion.p>

        <motion.div
          className="mt-8 flex gap-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.35 }}
        >
          <Link href="/dashboard">
            <Button size="lg" className="gap-2 text-base">
              Get Started
              <ChevronRight className="h-4 w-4" />
            </Button>
          </Link>
        </motion.div>
      </section>

      {/* Features */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto pb-24 w-full">
        {FEATURES.map((feature, i) => (
          <motion.div
            key={feature.title}
            className="rounded-xl border border-border/50 bg-card/30 p-6 hover:bg-card/60 transition-colors"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.4 + i * 0.1 }}
          >
            <feature.icon className="h-8 w-8 text-indigo-400 mb-3" />
            <h3 className="text-lg font-semibold mb-1">{feature.title}</h3>
            <p className="text-sm text-muted-foreground">{feature.desc}</p>
          </motion.div>
        ))}
      </section>
    </div>
  );
}
