"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import {
  Brain,
  Shield,
  Users,
  AlertTriangle,
  BarChart3,
  Target,
  Zap,
  ArrowRight,
  ChevronRight,
  Code2,
  GitBranch,
  Lock,
  Search,
  FileWarning,
  CheckCircle2,
  Layers,
  Fingerprint,
  Cpu,
  Eye,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

/* ── Animation Variants ── */
const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.6, ease: [0.22, 1, 0.36, 1] },
  }),
};

const fadeIn = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.8 } },
};

const scaleIn = {
  hidden: { opacity: 0, scale: 0.9 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.5, ease: "easeOut" } },
};

/* ── Data ── */
const problems = [
  {
    icon: Users,
    title: "Hiring Blind Spots",
    description:
      "Companies hire security engineers based on interviews alone. Resume claims go unverified against actual code quality.",
    color: "from-amber-500 to-orange-600",
  },
  {
    icon: AlertTriangle,
    title: "Security Tool Noise",
    description:
      "Traditional security scanners generate hundreds of alerts with no context. Teams suffer from alert fatigue and miss real threats.",
    color: "from-red-500 to-rose-600",
  },
];

const capabilities = [
  {
    icon: Shield,
    title: "Code Security Intelligence",
    description: "Multi-agent pipeline scans real codebases — AST parsing, static analysis, exploit simulation, and AI-driven reasoning.",
    color: "from-[hsl(170,80%,50%)] to-[hsl(155,70%,45%)]",
  },
  {
    icon: Brain,
    title: "Security Hiring Panel",
    description: "Evaluates candidates by scanning their actual repositories and comparing findings against resume claims.",
    color: "from-[hsl(260,60%,55%)] to-[hsl(280,70%,50%)]",
  },
  {
    icon: Fingerprint,
    title: "Skill Inflation Detection",
    description: 'Flags mismatches: resume says "security expert" but repo contains SQL injection and hardcoded secrets.',
    color: "from-[hsl(330,80%,60%)] to-[hsl(350,70%,55%)]",
  },
  {
    icon: BarChart3,
    title: "Security Intelligence Index",
    description: "0-100 composite score measuring exploitability, patch quality, secure coding patterns, and risk awareness.",
    color: "from-[hsl(38,90%,55%)] to-[hsl(25,85%,50%)]",
  },
];

const securityAgents = [
  { name: "Recon", icon: Search, color: "from-cyan-500 to-teal-500" },
  { name: "Static Analysis", icon: Code2, color: "from-blue-500 to-indigo-500" },
  { name: "Vulnerability", icon: AlertTriangle, color: "from-red-500 to-orange-500" },
  { name: "Exploit Sim", icon: Zap, color: "from-amber-500 to-yellow-500" },
  { name: "Patch Gen", icon: CheckCircle2, color: "from-green-500 to-emerald-500" },
  { name: "Risk Scoring", icon: BarChart3, color: "from-purple-500 to-violet-500" },
  { name: "Debate", icon: Users, color: "from-pink-500 to-rose-500" },
  { name: "Report", icon: FileWarning, color: "from-slate-400 to-zinc-500" },
];

const hiringAgents = [
  { name: "Resume Analyst", icon: Eye, color: "from-blue-500 to-cyan-500" },
  { name: "Repo Evaluator", icon: GitBranch, color: "from-green-500 to-emerald-500" },
  { name: "Contradiction Detector", icon: AlertTriangle, color: "from-red-500 to-rose-500" },
  { name: "Technical Depth", icon: Layers, color: "from-purple-500 to-pink-500" },
  { name: "Hiring Manager", icon: Users, color: "from-indigo-500 to-violet-500" },
  { name: "Consensus", icon: Target, color: "from-slate-400 to-zinc-500" },
];

const howItWorks = [
  {
    step: "01",
    title: "Upload",
    description: "Upload a codebase (ZIP or GitHub URL) for security analysis, or submit a candidate's resume + repo for evaluation.",
    icon: Code2,
  },
  {
    step: "02",
    title: "Analyze",
    description: "14+ autonomous agents run a multi-layer pipeline: AST parsing → static analysis → AI-driven deep reasoning → exploit simulation.",
    icon: Cpu,
  },
  {
    step: "03",
    title: "Verdicts",
    description: "Get actionable results: vulnerability reports with patches, security intelligence scores, and evidence-based hiring decisions.",
    icon: Sparkles,
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background overflow-hidden">
      {/* ─── Background Orbs ─── */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="floating-orb w-[500px] h-[500px] bg-[hsl(170,80%,50%)] top-[-10%] left-[10%] opacity-[0.03]" />
        <div className="floating-orb w-[400px] h-[400px] bg-[hsl(260,60%,55%)] top-[30%] right-[-5%] opacity-[0.03]" style={{ animationDelay: "3s" }} />
        <div className="floating-orb w-[300px] h-[300px] bg-[hsl(330,80%,60%)] bottom-[10%] left-[20%] opacity-[0.02]" style={{ animationDelay: "5s" }} />
      </div>

      {/* ─── Navigation ─── */}
      <nav className="fixed top-0 w-full z-50 bg-background/60 backdrop-blur-2xl border-b border-white/[0.04]">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[hsl(170,80%,50%)] to-[hsl(260,60%,55%)] flex items-center justify-center shadow-lg shadow-[hsl(170,80%,50%)]/20">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold tracking-tight">VERDEXA</span>
            <span className="hidden sm:inline text-xs text-muted-foreground border border-border/50 rounded-full px-2 py-0.5">
              v2.0
            </span>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/dashboard">
              <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
                Dashboard
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button size="sm" className="bg-gradient-to-r from-[hsl(170,80%,50%)] to-[hsl(200,70%,50%)] text-background font-semibold hover:opacity-90 transition-opacity">
                Get Started
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* ─── Hero Section ─── */}
      <section className="relative pt-32 pb-24 px-6 hero-gradient">
        <div className="max-w-5xl mx-auto text-center relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[hsl(170,80%,50%)]/10 border border-[hsl(170,80%,50%)]/20 text-[hsl(170,80%,60%)] text-sm mb-8">
              <Zap className="w-3.5 h-3.5" />
              Security Intelligence & Hiring Evaluation Platform
            </div>
            <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold tracking-tight mb-8 leading-[1.05]">
              Audit Code.
              <br />
              <span className="text-gradient">Evaluate Talent.</span>
            </h1>
            <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-12 leading-relaxed">
              An autonomous multi-agent platform that scans real codebases for vulnerabilities
              and evaluates developer security intelligence — with evidence, not guesswork.
            </p>
            <div className="flex items-center justify-center gap-4">
              <Link href="/dashboard">
                <Button size="lg" className="h-13 px-8 text-base bg-gradient-to-r from-[hsl(170,80%,50%)] to-[hsl(200,70%,50%)] text-background font-semibold hover:opacity-90 transition-all shadow-lg shadow-[hsl(170,80%,50%)]/20">
                  Launch Platform
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
              <Button variant="outline" size="lg" className="h-13 px-8 text-base border-white/10 hover:border-white/20 hover:bg-white/[0.03]">
                View Architecture
              </Button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ─── Problem Statement ─── */}
      <section className="py-24 px-6 section-gradient">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={fadeIn}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4">The Problem</h2>
            <p className="text-muted-foreground text-lg max-w-xl mx-auto">
              Security hiring and vulnerability detection are fundamentally broken.
            </p>
          </motion.div>
          <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            {problems.map((problem, i) => (
              <motion.div
                key={problem.title}
                custom={i}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                variants={fadeUp}
              >
                <Card className="glass-card-hover h-full border-destructive/10">
                  <CardContent className="p-8">
                    <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${problem.color} flex items-center justify-center mb-5 opacity-90`}>
                      <problem.icon className="w-6 h-6 text-white" />
                    </div>
                    <h3 className="text-xl font-semibold mb-3">{problem.title}</h3>
                    <p className="text-muted-foreground leading-relaxed">{problem.description}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Solution ─── */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={fadeIn}
            className="text-center mb-16"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[hsl(170,80%,50%)]/10 border border-[hsl(170,80%,50%)]/20 text-[hsl(170,80%,60%)] text-sm mb-6">
              <Shield className="w-3.5 h-3.5" />
              The Solution
            </div>
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              One Platform. <span className="text-gradient">Two Capabilities.</span>
            </h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Verdexa audits real code and evaluates real skill — combining secure code intelligence
              with autonomous security hiring evaluation.
            </p>
          </motion.div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {capabilities.map((cap, i) => (
              <motion.div
                key={cap.title}
                custom={i}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                variants={fadeUp}
              >
                <Card className="glass-card-hover h-full group">
                  <CardContent className="p-6">
                    <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${cap.color} flex items-center justify-center mb-4 opacity-80 group-hover:opacity-100 transition-opacity`}>
                      <cap.icon className="w-5 h-5 text-white" />
                    </div>
                    <h3 className="font-semibold mb-2 text-[15px]">{cap.title}</h3>
                    <p className="text-muted-foreground text-sm leading-relaxed">{cap.description}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── How It Works ─── */}
      <section className="py-24 px-6 section-gradient">
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={fadeIn}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4">How It Works</h2>
            <p className="text-muted-foreground text-lg">Three steps. Fully autonomous.</p>
          </motion.div>
          <div className="grid md:grid-cols-3 gap-6">
            {howItWorks.map((step, i) => (
              <motion.div
                key={step.step}
                custom={i}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                variants={fadeUp}
              >
                <div className="glass-card p-8 h-full relative overflow-hidden group">
                  <div className="absolute top-4 right-4 text-6xl font-black text-white/[0.03] group-hover:text-[hsl(170,80%,50%)]/[0.06] transition-colors">
                    {step.step}
                  </div>
                  <div className="w-11 h-11 rounded-xl bg-[hsl(170,80%,50%)]/10 flex items-center justify-center mb-5">
                    <step.icon className="w-5 h-5 text-[hsl(170,80%,60%)]" />
                  </div>
                  <h3 className="text-lg font-bold mb-3">{step.title}</h3>
                  <p className="text-muted-foreground text-sm leading-relaxed">{step.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Architecture: Security Pipeline ─── */}
      <section className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeIn}>
            <Card className="glass-card p-8 glow-border overflow-hidden">
              <div className="text-center mb-8">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[hsl(170,80%,50%)]/10 border border-[hsl(170,80%,50%)]/20 text-[hsl(170,80%,60%)] text-xs mb-4">
                  <Shield className="w-3 h-3" />
                  Security Pipeline
                </div>
                <h2 className="text-2xl font-bold mb-2">Multi-Agent Security Architecture</h2>
                <p className="text-muted-foreground text-sm">
                  14 autonomous agents working in concert to analyze code
                </p>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {securityAgents.map((agent, i) => (
                  <motion.div
                    key={agent.name}
                    custom={i}
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true }}
                    variants={fadeUp}
                  >
                    <div className="glass-card-hover p-4 text-center group cursor-default">
                      <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${agent.color} mx-auto mb-3 flex items-center justify-center opacity-70 group-hover:opacity-100 transition-all group-hover:scale-110`}>
                        <agent.icon className="w-5 h-5 text-white" />
                      </div>
                      <p className="text-xs font-medium text-muted-foreground group-hover:text-foreground transition-colors">{agent.name}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
              <div className="flex items-center justify-center mt-8 gap-2 text-muted-foreground text-xs">
                {["Recon", "Parse", "Analyze", "Exploit", "Patch", "Score", "Debate", "Report"].map((step, i) => (
                  <span key={step} className="flex items-center gap-1.5">
                    {i > 0 && <ChevronRight className="w-3 h-3 text-[hsl(170,80%,50%)]/40" />}
                    <span>{step}</span>
                  </span>
                ))}
              </div>
            </Card>
          </motion.div>
        </div>
      </section>

      {/* ─── Architecture: Hiring Pipeline ─── */}
      <section className="py-12 px-6">
        <div className="max-w-5xl mx-auto">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeIn}>
            <Card className="glass-card p-8 overflow-hidden">
              <div className="text-center mb-8">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[hsl(260,60%,55%)]/10 border border-[hsl(260,60%,55%)]/20 text-[hsl(260,60%,65%)] text-xs mb-4">
                  <Brain className="w-3 h-3" />
                  Hiring Pipeline
                </div>
                <h2 className="text-2xl font-bold mb-2">Security Hiring Evaluation Panel</h2>
                <p className="text-muted-foreground text-sm">
                  Autonomous agents evaluate candidates against real code evidence
                </p>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {hiringAgents.map((agent, i) => (
                  <motion.div
                    key={agent.name}
                    custom={i}
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true }}
                    variants={fadeUp}
                  >
                    <div className="glass-card-hover p-4 text-center group cursor-default">
                      <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${agent.color} mx-auto mb-3 flex items-center justify-center opacity-70 group-hover:opacity-100 transition-all group-hover:scale-110`}>
                        <agent.icon className="w-5 h-5 text-white" />
                      </div>
                      <p className="text-xs font-medium text-muted-foreground group-hover:text-foreground transition-colors">{agent.name}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </Card>
          </motion.div>
        </div>
      </section>

      {/* ─── Skill Inflation Feature Highlight ─── */}
      <section className="py-24 px-6 section-gradient">
        <div className="max-w-5xl mx-auto">
          <div className="grid md:grid-cols-2 gap-10 items-center">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[hsl(330,80%,60%)]/10 border border-[hsl(330,80%,60%)]/20 text-[hsl(330,80%,70%)] text-xs mb-5">
                <Fingerprint className="w-3 h-3" />
                Core Differentiator
              </div>
              <h2 className="text-3xl font-bold mb-4">Skill Inflation Detection</h2>
              <p className="text-muted-foreground leading-relaxed mb-6">
                Verdexa compares resume claims against actual repository findings.
                When a candidate claims &quot;Expert in secure backend systems&quot; but their code contains SQL injection and hardcoded secrets — the system flags it.
              </p>
              <div className="space-y-3">
                {[
                  "Cross-references resume security keywords with vulnerability findings",
                  "Rates mismatch severity: minor, moderate, significant inflation",
                  "Generates evidence-based contradiction reports",
                ].map((point, i) => (
                  <div key={i} className="flex items-start gap-3 text-sm">
                    <CheckCircle2 className="w-4 h-4 text-[hsl(170,80%,50%)] mt-0.5 shrink-0" />
                    <span className="text-muted-foreground">{point}</span>
                  </div>
                ))}
              </div>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <div className="glass-card p-6 space-y-4 neon-glow-purple">
                <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                  <span className="font-medium text-amber-400">Skill Mismatch Detected</span>
                </div>
                <div className="space-y-3">
                  <div className="glass-card p-3">
                    <span className="text-xs text-muted-foreground">Resume Claim</span>
                    <p className="text-sm font-medium mt-1">&quot;Expert in secure backend systems and OWASP Top 10&quot;</p>
                  </div>
                  <div className="glass-card p-3 border-red-500/20">
                    <span className="text-xs text-red-400">Repository Evidence</span>
                    <div className="mt-2 space-y-1.5">
                      <div className="flex items-center gap-2 text-xs">
                        <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                        <span>SQL Injection in auth/login.py</span>
                      </div>
                      <div className="flex items-center gap-2 text-xs">
                        <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                        <span>Hardcoded API keys in config.py</span>
                      </div>
                      <div className="flex items-center gap-2 text-xs">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                        <span>No input validation in API routes</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-xs px-1">
                    <span className="text-muted-foreground">Inflation Score</span>
                    <span className="text-red-400 font-bold">72 / 100</span>
                  </div>
                  <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-amber-500 to-red-500 rounded-full"
                      initial={{ width: 0 }}
                      whileInView={{ width: "72%" }}
                      viewport={{ once: true }}
                      transition={{ duration: 1, delay: 0.5 }}
                    />
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ─── CTA Section ─── */}
      <section className="py-24 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-5">
              Ready to See the <span className="text-gradient">Truth</span>?
            </h2>
            <p className="text-muted-foreground text-lg mb-10 max-w-lg mx-auto">
              Upload a codebase or candidate profile. Let the agents analyze, debate, and deliver evidence-based verdicts.
            </p>
            <div className="flex items-center justify-center gap-4">
              <Link href="/dashboard">
                <Button size="lg" className="h-13 px-10 text-base bg-gradient-to-r from-[hsl(170,80%,50%)] to-[hsl(200,70%,50%)] text-background font-semibold hover:opacity-90 transition-all shadow-lg shadow-[hsl(170,80%,50%)]/20">
                  Start Scanning
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
              <Link href="/dashboard">
                <Button variant="outline" size="lg" className="h-13 px-10 text-base border-white/10 hover:border-white/20">
                  Evaluate Candidates
                  <Brain className="w-4 h-4 ml-2" />
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ─── Footer ─── */}
      <footer className="border-t border-white/[0.04] py-8 px-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-sm text-muted-foreground">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[hsl(170,80%,50%)] to-[hsl(260,60%,55%)] flex items-center justify-center">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold text-foreground">VERDEXA</span>
            <span className="text-xs">&middot; Security Intelligence & Hiring Evaluation</span>
          </div>
          <span className="text-xs opacity-70">Built with multi-agent AI architecture</span>
        </div>
      </footer>
    </div>
  );
}
