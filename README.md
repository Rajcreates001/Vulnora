# Vulnora - Autonomous Security Research Agent

An AI-powered autonomous security research system that analyzes codebases, discovers vulnerabilities, simulates exploits, generates patches, and produces professional security reports.

## Architecture

```
Frontend (Next.js) → FastAPI Backend → LangGraph Agent Orchestra → LLM + Analysis Tools → DB Layer
```

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- Redis
- Supabase account (free tier works)

**Database setup:** Run `backend/db/schema.sql` in your Supabase project's SQL Editor to create tables (projects, files, vulnerabilities, agent_logs).

### Setup

1. Clone and configure environment:

**Backend** (copy to `backend/.env`):
```bash
cp .env.example backend/.env
# Fill in OPENAI_API_KEY or ANTHROPIC_API_KEY, Supabase, Redis, etc.
# For local dev without auth: VULNORA_DEV_AUTH_BYPASS=1 (already in .env.example)
```

**Frontend** (create `frontend/.env.local`):
```bash
# Create frontend/.env.local with:
NEXT_PUBLIC_API_URL=http://localhost:8000
```

2. Start with Docker:
```bash
docker-compose up --build
```

3. Or run manually:

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

4. Open http://localhost:3000

## Features
- Multi-agent autonomous security analysis
- Vulnerability discovery (SQLi, XSS, Auth flaws, Secrets, etc.)
- Exploit simulation with Proof-of-Exploit generation
- Automated patch generation
- Interactive attack path visualization
- Professional security reports
- Agent reasoning transparency logs

## Tech Stack
- **Frontend:** Next.js 14, TypeScript, Tailwind CSS, ShadCN UI, Framer Motion, React Flow
- **Backend:** Python FastAPI, LangGraph, OpenAI/Anthropic LLMs
- **Database:** Supabase (PostgreSQL), ChromaDB, Redis
