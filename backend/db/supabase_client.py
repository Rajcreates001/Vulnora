"""Supabase database client and operations."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from supabase import create_client, Client

from config import settings


_client: Optional[Client] = None


def get_supabase() -> Client:
    """Get or create Supabase client singleton."""
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return _client


def gen_id() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Projects ────────────────────────────────────────

async def create_project(name: str, repo_path: Optional[str] = None) -> Dict[str, Any]:
    db = get_supabase()
    project = {
        "id": gen_id(),
        "name": name,
        "repo_path": repo_path,
        "scan_status": "pending",
        "created_at": now_iso(),
    }
    result = db.table("projects").insert(project).execute()
    return result.data[0] if result.data else project


async def get_project(project_id: str) -> Optional[Dict[str, Any]]:
    db = get_supabase()
    result = db.table("projects").select("*").eq("id", project_id).execute()
    return result.data[0] if result.data else None


async def get_projects() -> List[Dict[str, Any]]:
    db = get_supabase()
    result = db.table("projects").select("*").order("created_at", desc=True).execute()
    return result.data or []


async def update_project(project_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    db = get_supabase()
    result = db.table("projects").update(updates).eq("id", project_id).execute()
    return result.data[0] if result.data else {}


async def delete_project(project_id: str) -> bool:
    db = get_supabase()
    result = db.table("projects").delete().eq("id", project_id).execute()
    return bool(result.data)

# ─── Files ────────────────────────────────────────────

async def store_file(project_id: str, file_path: str, content: str, language: Optional[str] = None) -> Dict[str, Any]:
    db = get_supabase()
    file_record = {
        "id": gen_id(),
        "project_id": project_id,
        "file_path": file_path,
        "content": content,
        "language": language or detect_language(file_path),
        "size": len(content),
        "created_at": now_iso(),
    }
    result = db.table("files").insert(file_record).execute()
    return result.data[0] if result.data else file_record


async def get_project_files(project_id: str) -> List[Dict[str, Any]]:
    db = get_supabase()
    result = db.table("files").select("*").eq("project_id", project_id).execute()
    return result.data or []


async def get_file_content(file_id: str) -> Optional[Dict[str, Any]]:
    db = get_supabase()
    result = db.table("files").select("*").eq("id", file_id).execute()
    return result.data[0] if result.data else None


# ─── Vulnerabilities ─────────────────────────────────

async def store_vulnerability(vuln: Dict[str, Any]) -> Dict[str, Any]:
    db = get_supabase()
    vuln["id"] = vuln.get("id", gen_id())
    vuln["created_at"] = vuln.get("created_at", now_iso())
    result = db.table("vulnerabilities").insert(vuln).execute()
    return result.data[0] if result.data else vuln


async def get_vulnerabilities(project_id: str) -> List[Dict[str, Any]]:
    db = get_supabase()
    result = (
        db.table("vulnerabilities")
        .select("*")
        .eq("project_id", project_id)
        .order("risk_score", desc=True)
        .execute()
    )
    return result.data or []


async def get_vulnerability(vuln_id: str) -> Optional[Dict[str, Any]]:
    db = get_supabase()
    result = db.table("vulnerabilities").select("*").eq("id", vuln_id).execute()
    return result.data[0] if result.data else None


# ─── Agent Logs ───────────────────────────────────────

async def store_agent_log(
    project_id: str,
    agent_name: str,
    message: str,
    log_type: str = "info",
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    db = get_supabase()
    log_record = {
        "id": gen_id(),
        "project_id": project_id,
        "agent_name": agent_name,
        "message": message,
        "log_type": log_type,
        "data": data or {},
        "timestamp": now_iso(),
    }
    result = db.table("agent_logs").insert(log_record).execute()
    return result.data[0] if result.data else log_record


async def get_agent_logs(project_id: str) -> List[Dict[str, Any]]:
    db = get_supabase()
    result = (
        db.table("agent_logs")
        .select("*")
        .eq("project_id", project_id)
        .order("timestamp")
        .execute()
    )
    return result.data or []


# ─── Helpers ──────────────────────────────────────────

def detect_language(file_path: str) -> str:
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".jsx": "javascript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".cs": "csharp",
        ".sql": "sql",
        ".html": "html",
        ".css": "css",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".json": "json",
        ".xml": "xml",
        ".sh": "bash",
        ".env": "env",
        ".md": "markdown",
    }
    for ext, lang in ext_map.items():
        if file_path.endswith(ext):
            return lang
    return "unknown"
