"""Verdexa — Security Intelligence & Hiring Evaluation Platform."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import get_settings
from db.database import engine, Base
from routes import candidates, evaluations, agent_logs
from routes import interview
from routes import scanning, projects, url_scan


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # Startup: create database tables (best-effort — app can still serve non-DB routes)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Database connection failed at startup: {e}. DB-dependent routes will fail.")
    yield
    # Shutdown: dispose engine
    try:
        await engine.dispose()
    except Exception:
        pass


settings = get_settings()

app = FastAPI(
    title="Verdexa",
    description="Security Intelligence & Hiring Evaluation Platform — Unified code security auditing and developer assessment",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "verdexa", "version": "2.0.0"}


# Register Routers — Hiring Intelligence
app.include_router(candidates.router, prefix="/api", tags=["Candidates"])
app.include_router(evaluations.router, prefix="/api", tags=["Evaluations"])
app.include_router(agent_logs.router, prefix="/api", tags=["Agent Logs"])
app.include_router(interview.router, prefix="/api", tags=["Interview"])

# Register Routers — Security Intelligence
app.include_router(scanning.router, tags=["Security Scanning"])
app.include_router(projects.router, tags=["Projects"])
app.include_router(url_scan.router, tags=["URL / Website Scan"])
