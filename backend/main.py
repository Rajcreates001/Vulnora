"""Vulnora - Autonomous Security Research Agent - Backend API."""

import os
from contextlib import asynccontextmanager


from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import settings
from routes.projects import router as projects_router
from routes.scanning import router as scanning_router

import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # Startup
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.chroma_persist_dir, exist_ok=True)
    print("[*] Vulnora Backend Starting...")
    print(f"   LLM Provider: {settings.llm_provider}")
    print(f"   Upload Dir: {settings.upload_dir}")
    print(f"   VULNORA_DEV_AUTH_BYPASS: {os.environ.get('VULNORA_DEV_AUTH_BYPASS', '0')}")
    yield
    # Shutdown
    print("[*] Vulnora Backend Shutting Down...")



# --- Logging setup ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("vulnora")

# --- Rate limiting setup ---
limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute", "200/hour"])

app = FastAPI(
    title="Vulnora - Autonomous Security Research Agent",
    description="AI-powered autonomous security analysis system",
    version="1.0.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS (allow credentials, all methods, all headers, configurable origins)
origins = [o.strip() for o in settings.backend_cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Logging middleware ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url.path} from {request.client.host}")
    try:
        response = await call_next(request)
        logger.info(f"{request.method} {request.url.path} - {response.status_code}")
        return response
    except Exception as exc:
        logger.error(f"Error handling {request.method} {request.url.path}: {exc}")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# --- Global error handler for validation and HTTP errors ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# Routes
app.include_router(projects_router)
app.include_router(scanning_router)


# --- Dev Auth Bypass Check Endpoint ---
@app.get("/api/dev-auth-check")
async def dev_auth_check():
    """Check if dev auth bypass is active."""
    return {
        "VULNORA_DEV_AUTH_BYPASS": os.environ.get("VULNORA_DEV_AUTH_BYPASS", "0"),
        "bypass_active": os.environ.get("VULNORA_DEV_AUTH_BYPASS", "0") == "1"
    }



# --- Health and root endpoints (no auth/rate limit) ---
@app.get("/")
async def root():
    return {
        "name": "Vulnora",
        "description": "Autonomous Security Research Agent",
        "version": "1.0.0",
        "status": "operational",
    }



@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
    )
