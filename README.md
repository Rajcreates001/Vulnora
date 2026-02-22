# VERDEXA — Security Intelligence & Hiring Evaluation Platform

An enterprise-grade platform that combines **autonomous hiring intelligence** with **code and website security scanning**. Verdexa evaluates candidates through resume analysis, interview simulation, AI agent debates, and simultaneously audits codebases and websites for vulnerabilities using multi-agent pipelines.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Frontend Pages](#frontend-pages)
- [Multi-Agent Panels](#multi-agent-panels)
- [Environment Configuration](#environment-configuration)
- [Getting Started](#getting-started)
- [Deployment](#deployment)

---

## Overview

Verdexa provides two integrated pillars:

1. **Security Hiring Intelligence (AHIP)** — Simulates a technical hiring committee. Evaluates candidates via resume analysis, interview transcript evaluation, contradiction detection, skill gap analysis, agent debates, and produces explainable hiring decisions with confidence and risk scores.

2. **Security Intelligence** — Code security auditing (upload ZIP or GitHub repo) and website security scanning (URL-based crawl and vulnerability testing). Multi-agent pipeline includes recon, static analysis, vulnerability detection, exploit simulation, and patch generation.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js 14 + App Router)               │
│  TypeScript • Tailwind CSS • ShadCN UI • Framer Motion • Zustand    │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │ HTTP / SSE
┌──────────────────────────────────▼──────────────────────────────────┐
│                        Backend API (FastAPI)                         │
│  Candidates │ Evaluations │ Interview │ Projects │ Scanning │ URL   │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
┌───────▼───────┐         ┌────────▼────────┐         ┌──────▼──────┐
│ Hiring Graph  │         │ Security Graph  │         │ URL Scan    │
│  (LangGraph)  │         │   (LangGraph)   │         │ (Crawler +  │
│ 8 AI Agents   │         │ 14 AI Agents    │         │  Scanner)   │
└───────┬───────┘         └────────┬────────┘         └──────┬──────┘
        │                          │                          │
        └──────────────────────────┼──────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────┐
│  PostgreSQL (Candidates/Evaluations) │ Supabase │ Redis │ ChromaDB  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Features

### Security Hiring Intelligence

| Feature | Description |
|---------|-------------|
| **Add Candidate** | Upload resume (PDF/DOCX/TXT) or paste text, plus job description |
| **Live Evaluation** | Stream evaluation progress with SSE; watch agents analyze in real time |
| **Interview Mode** | AI-driven technical interview with time-limited questions and scoring |
| **Evaluation Report** | Technical, behavioral, domain, and communication scores; skill gaps; contradictions; risk analysis |
| **Agent Debate** | View consensus-building between hiring agents |
| **Why Not Hire** | Evidence-based weaknesses, improvement suggestions, 30-day plan |
| **Re-evaluate / Reset** | Reset candidate status and run evaluation again |

### Code Security Scanning

| Feature | Description |
|---------|-------------|
| **Upload Repository** | ZIP file or GitHub URL |
| **Multi-Agent Scan** | Recon → Static Analysis → Vulnerability → Exploit → Patch → Report |
| **Scan Results** | Vulnerabilities, attack paths, risk charts, agent logs |
| **Live Chat** | SSE stream of agent activity during scan |
| **Security Intelligence Index** | Aggregate exploitability, patch quality, secure coding, complexity |
| **Candidate Repo Scan** | Link a candidate’s repo to their profile; detect skill inflation vs. code |

### Website Security Scanning

| Feature | Description |
|---------|-------------|
| **URL Scan** | Enter URL to crawl and test (SQLi, XSS, path traversal, open redirect, etc.) |
| **Scan Progress** | Crawling → Scanning → Analyzing → Complete |
| **Vulnerability Report** | Findings with payload, evidence, patch recommendation |
| **Attack Paths** | Visual representation of exploitation paths |
| **Discovered Endpoints** | Pages, forms, API endpoints found during crawl |

---

## Tech Stack

### Frontend

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS, ShadCN UI
- **State:** Zustand
- **Animations:** Framer Motion
- **Charts:** Recharts
- **Icons:** Lucide React

### Backend

- **Framework:** FastAPI + Uvicorn
- **Orchestration:** LangGraph (hiring + security graphs)
- **LLM:** OpenAI (GPT-4o), Anthropic (Claude), Groq, Ollama
- **DB:** PostgreSQL (asyncpg), Supabase
- **Cache:** Redis
- **Vector Store:** ChromaDB

### Code & Security

- **Parsing:** tree-sitter (Python, JavaScript, TypeScript)
- **Static Analysis:** Bandit, custom heuristics
- **Web Scan:** BeautifulSoup, Playwright
- **File Handling:** PyPDF2, python-docx, aiofiles

---

## Project Structure

```
Verdexa/
├── backend/
│   ├── agents/              # AI agents (hiring + security)
│   │   ├── resume_analyst.py
│   │   ├── technical_depth.py
│   │   ├── behavioral_psychologist.py
│   │   ├── domain_expert.py
│   │   ├── contradiction_detector.py
│   │   ├── hiring_manager.py
│   │   ├── bias_auditor.py
│   │   ├── consensus_negotiator.py
│   │   ├── recon_agent.py
│   │   ├── vulnerability_agent.py
│   │   └── ...
│   ├── db/                  # Database clients
│   ├── graph/               # LangGraph workflows
│   ├── models/              # Pydantic + SQLAlchemy models
│   ├── routes/              # API routes
│   ├── services/            # Business logic
│   ├── utils/               # Helpers, LLM client, auth
│   ├── webscan/             # URL scan (crawler, scanner, analyzer)
│   ├── config.py
│   └── main.py
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # Landing page
│   │   ├── dashboard/       # Dashboard (candidates + projects)
│   │   ├── evaluation/      # Evaluation report
│   │   ├── interview/       # Interview session
│   │   ├── results/         # Code scan results
│   │   └── webscan/         # Website scan results
│   ├── components/
│   ├── lib/
│   └── store/
└── README.md
```

---

## API Reference

All API routes are prefixed with `/api` unless noted. Base URL: `http://localhost:8000`.

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |

### Candidates (Hiring)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload-candidate` | Upload candidate (JSON: name, email, resume_text, transcript_text, job_description) |
| POST | `/api/upload-candidate-files` | Upload candidate with files (FormData: name, email, job_description, resume, transcript) |
| GET | `/api/candidates` | List all candidates |
| GET | `/api/candidates/{id}` | Get candidate details |
| DELETE | `/api/candidates/{id}` | Delete candidate |
| PATCH | `/api/candidates/{id}/reset` | Reset status to pending (re-evaluate) |

### Evaluations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/run-evaluation` | Run full evaluation pipeline (non-streaming) |
| GET | `/api/run-evaluation-stream/{candidate_id}` | SSE stream of evaluation progress |
| GET | `/api/evaluation-results/{candidate_id}` | Get evaluation results |
| GET | `/api/evaluations` | List all evaluations |

### Agent Logs (Candidates)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/agent-logs/{candidate_id}` | Get agent logs for a candidate |

### Interview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/interview/start` | Start interview session |
| POST | `/api/interview/answer` | Submit answer |
| POST | `/api/interview/end/{session_id}` | End interview |
| GET | `/api/interview/end-and-evaluate/{session_id}` | End and run evaluation (SSE) |
| GET | `/api/interview/session/{session_id}` | Get session |
| GET | `/api/interview/transcript/{session_id}` | Get transcript |
| POST | `/api/resume/extract` | Extract structured data from resume text |

### Projects (Code Security)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload-repo` | Upload ZIP or GitHub URL (FormData: project_name, file, repo_url) |
| GET | `/api/projects` | List projects |
| GET | `/api/projects/{id}` | Get project details |
| DELETE | `/api/projects/{id}` | Delete project |
| GET | `/api/files/{file_id}` | Get file content |

### Scanning (Code Security)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/start-scan` | Start scan (body: project_id, force?) |
| GET | `/api/scan-status/{project_id}` | Get scan status |
| GET | `/api/results/{project_id}` | Get scan results (vulnerabilities, report, attack paths) |
| GET | `/api/project-logs/{project_id}` | Get project agent logs |
| GET | `/api/scan-stream/{project_id}` | SSE stream of scan progress |
| GET | `/api/report/{project_id}` | Get detailed security report |
| GET | `/api/security-intelligence/{project_id}` | Get Security Intelligence Index |
| GET | `/api/vulnerabilities/{vuln_id}` | Get vulnerability detail |
| POST | `/api/candidate-repo-scan` | Scan candidate repo (body: candidate_id, project_id, resume_text) |

### URL / Website Scan

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/scan/url` | Start URL scan (body: url) |
| POST | `/api/scan/url-with-auth` | Start URL scan with login (body: url, credentials) |
| GET | `/api/url-scan-status/{scan_id}` | Get scan status |
| GET | `/api/url-results/{scan_id}` | Get full results |
| GET | `/api/url-vulnerabilities/{vuln_id}` | Get vulnerability detail |

---

## Frontend Pages

| Route | Description |
|-------|-------------|
| `/` | Landing page |
| `/dashboard` | Dashboard: Code Security + Security Hiring tabs |
| `/evaluation/[id]` | Evaluation report (scores, debate, contradictions, skill gaps) |
| `/evaluation/[id]?live=true` | Live evaluation stream |
| `/interview/[id]` | AI interview session |
| `/results/[projectId]` | Code scan results (vulnerabilities, attack paths, charts) |
| `/webscan/[scanId]` | Website scan results |

---

## Multi-Agent Panels

### Hiring Panel (8 Agents)

| Agent | Role |
|-------|------|
| Resume Analyst | Extract and evaluate resume claims |
| Technical Depth Analyst | Assess technical knowledge depth |
| Behavioral Psychologist | Evaluate soft skills and communication |
| Domain Expert | Validate domain-specific expertise |
| Contradiction Detector | Flag resume vs transcript discrepancies |
| Hiring Manager | Business fit and team alignment |
| Bias Auditor | Ensure fair, unbiased evaluation |
| Consensus Negotiator | Synthesize final hiring decision |

### Security Scan Panel (14 Agents)

| Agent | Role |
|-------|------|
| Recon Agent | Discover files, endpoints, structure |
| Parser Agent | Parse code with tree-sitter |
| Static Analysis Agent | AST-based static analysis |
| Heuristic Agent | Rule-based vulnerability checks |
| Vulnerability Agent | Classify and score vulnerabilities |
| Exploit Agent | Simulate exploitation paths |
| Patch Agent | Generate remediation patches |
| Report Agent | Executive summary and report |
| Alert Reduction Agent | Reduce false positives |
| Missed Vuln Reasoning | Explain why tools miss vulnerabilities |
| Debate Agent | Security-focused agent debate |
| Risk Agent | Risk assessment |
| Graph Agent | Attack path modeling |
| Insight Agent | Strategic insights |

---

## Environment Configuration

Create `backend/.env` and `frontend/.env.local` from `.env.example`.

### Backend `.env`

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | — |
| `ANTHROPIC_API_KEY` | Anthropic API key | — |
| `GROQ_API_KEY` | Groq API key | — |
| `LLM_PROVIDER` | openai \| anthropic \| groq \| ollama | openai |
| `LLM_MODEL` | Model name | gpt-4o |
| `DATABASE_URL` | PostgreSQL connection string | — |
| `SUPABASE_URL` | Supabase project URL | — |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | — |
| `REDIS_URL` | Redis connection | redis://localhost:6379/0 |
| `CHROMA_PERSIST_DIR` | ChromaDB directory | ./chroma_data |
| `CORS_ORIGINS` | Allowed origins (comma-separated) | http://localhost:3000 |
| `GITHUB_TOKEN` | GitHub token (optional, for private repos) | — |

### Frontend `.env.local`

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | http://localhost:8000 |

---

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.10+
- PostgreSQL (or Supabase)
- Redis
- (Optional) Supabase for projects and URL scans

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys and database URLs
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000 in .env.local
npm run dev
```

If port 3000 is in use:

```bash
npm run dev -- -p 3001
```

### Database Setup

- **Candidates & Evaluations:** Uses `DATABASE_URL` (PostgreSQL). Tables are created automatically on startup.
- **Projects & URL Scans:** Use Supabase. If `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are not set, project upload and URL scan features are disabled; hiring features still work.

---

## Deployment

- **Frontend:** Vercel, Netlify, or static export
- **Backend:** Render, Railway, Fly.io, or any Python host
- **Database:** Supabase, Railway PostgreSQL, etc.
- **Redis:** Upstash, Redis Cloud, or self-hosted

Ensure `CORS_ORIGINS` includes your frontend URL and `NEXT_PUBLIC_API_URL` points to your deployed backend.

---

## License

MIT
