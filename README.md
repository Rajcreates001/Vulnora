# Vulnora - Hybrid Security Intelligence Engine

An autonomous DevSecOps research system combining **Deterministic Analysis** with **AI Agent Reasoning**. It analyzes codebases, discovers vulnerabilities, simulates exploits, generates patches, and produces professional security reports while aggressively minimizing LLM token cost and alert fatigue.

## Architecture

```
Frontend (Next.js) → FastAPI Backend → 12-Layer Intelligence Pipeline → DB Layer
```

**The Hybrid Pipeline:**
1. **Layer 1 (Parser):** AST Parsing via `tree-sitter`
2. **Layer 2 (Static):** Fast local scanning via `bandit`
3. **Layer 3 (Graph):** Dependency Reachability via `networkx`
4. **Layer 4 (Heuristic):** Rule-based risk scoring overlays
5. **Layer 5 (AI Agents):** LLM-driven deep flaw detection, patching, and human-level insights
6. **Alert Reduction:** Deduplication & alert fatigue minimization

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- Redis
- Supabase account (free tier works)
- **Ollama** (optional, for offline local LLM execution)

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
- **Deterministic First:** Relies on AST parsing and Static tools to eliminate base noise before consuming expensive LLM tokens.
- **Dependency Graph Reasoning:** NetworkX-backed reachability validation.
- **Offline AI Support:** Integrated directly with Ollama for zero-cost remote execution (`llama3`, `mistral`).
- Multi-agent autonomous security analysis (LangGraph)
- Exploit simulation with Proof-of-Exploit generation
- Automated patch generation
- Alert Fatigue Minimization Engine
- Human-Level Insight Generator ("Why this was missed")
- Interactive attack path visualization
- Professional security reports
- Agent reasoning transparency logs

## Tech Stack
- **Frontend:** Next.js 14, TypeScript, Tailwind CSS, ShadCN UI, Framer Motion, React Flow
- **Backend:** Python FastAPI, LangGraph, Ollama, OpenAI/Anthropic/Groq LLMs
- **Deterministic:** Tree-Sitter, NetworkX, Bandit
- **Database:** Supabase (PostgreSQL), ChromaDB, Redis
