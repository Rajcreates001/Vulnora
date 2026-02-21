from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # LLM
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_provider: str = "openai"

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    database_url: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # ChromaDB
    chroma_persist_dir: str = "./data/chromadb"

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_cors_origins: str = "http://localhost:3000"

    # Upload
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 100

    # GitHub
    github_token: Optional[str] = None

    # Auth
    jwt_secret: str = "change-this-secret-in-prod"
    jwt_algorithm: str = "HS256"
    api_key: Optional[str] = None  # Set to a strong value in .env for API key auth

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
