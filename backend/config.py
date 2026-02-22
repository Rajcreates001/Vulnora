from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Unified application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # ─── API Keys ────────────────────────────────────────────
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    groq_api_key: str = ""

    # ─── LLM Configuration ──────────────────────────────────
    llm_provider: str = "openai"          # openai | anthropic | groq | ollama
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 8192

    # ─── Ollama (Local/Offline LLM) ─────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # ─── Database (Supabase PostgreSQL) ─────────────────────
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/verdexa"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # ─── Redis ──────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ─── ChromaDB ───────────────────────────────────────────
    chroma_persist_dir: str = "./chroma_data"

    # ─── Server ─────────────────────────────────────────────
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001"

    # ─── Upload ─────────────────────────────────────────────
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 100

    # ─── GitHub ─────────────────────────────────────────────
    github_token: Optional[str] = None

    # ─── Auth ───────────────────────────────────────────────
    jwt_secret: str = "change-this-secret-in-prod"
    jwt_algorithm: str = "HS256"
    api_key: Optional[str] = None
    vulnora_dev_auth_bypass: str = "0"

    # ─── App ────────────────────────────────────────────────
    app_name: str = "Verdexa"
    debug: bool = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Backward-compatible alias
settings = get_settings()
