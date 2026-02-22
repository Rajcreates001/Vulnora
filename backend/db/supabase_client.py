"""Supabase database client and operations."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from supabase import create_client, Client

from config import settings


_client: Optional[Client] = None
_supabase_available: Optional[bool] = None


def get_supabase() -> Optional[Client]:
    """Get or create Supabase client singleton. Returns None if Supabase is not configured."""
    global _client, _supabase_available
    if _supabase_available is False:
        return None
    if _client is None:
        url = (settings.supabase_url or "").strip()
        key = (settings.supabase_service_role_key or "").strip()
        if not url or not key:
            _supabase_available = False
            return None
        try:
            _client = create_client(url, key)
            _supabase_available = True
        except Exception as e:
            _supabase_available = False
            print(f"[Supabase] Client init failed: {e}. Supabase features disabled.")
            return None
    return _client


def gen_id() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Projects ────────────────────────────────────────

async def create_project(name: str, repo_path: Optional[str] = None) -> Dict[str, Any]:
    db = get_supabase()
    if not db:
        raise RuntimeError("Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env")
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
    if not db:
        return None
    result = db.table("projects").select("*").eq("id", project_id).execute()
    return result.data[0] if result.data else None


async def get_projects() -> List[Dict[str, Any]]:
    db = get_supabase()
    if not db:
        return []
    result = db.table("projects").select("*").order("created_at", desc=True).execute()
    return result.data or []


async def update_project(project_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    db = get_supabase()
    if not db:
        return {}
    result = db.table("projects").update(updates).eq("id", project_id).execute()
    return result.data[0] if result.data else {}


async def delete_project(project_id: str) -> bool:
    db = get_supabase()
    if not db:
        return False
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


async def delete_vulnerabilities_by_project(project_id: str) -> None:
    """Remove all vulnerabilities for a project (e.g. before re-scan or incremental persist)."""
    db = get_supabase()
    db.table("vulnerabilities").delete().eq("project_id", project_id).execute()


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
    """Store agent log. Returns empty dict if storage fails (non-critical)."""
    try:
        db = get_supabase()
        # Ensure message isn't too long for database
        if len(message) > 10000:
            message = message[:10000] + "... [truncated]"
        
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
    except Exception as e:
        # Logging failures shouldn't stop the scan
        print(f"[LOG ERROR] Failed to store agent log for {project_id}/{agent_name}: {e}")
        # Return empty dict so calling code doesn't break
        return {}
    except Exception as e:
        # Logging failures shouldn't stop the scan
        print(f"[LOG ERROR] Failed to store agent log for {project_id}/{agent_name}: {e}")
        # Return empty dict so calling code doesn't break
        return {}


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


# ─── URL Scans (Website Security) ────────────────────

async def create_url_scan(target_url: str) -> Dict[str, Any]:
    db = get_supabase()
    row = {
        "id": gen_id(),
        "target_url": target_url,
        "status": "pending",
        "security_posture_score": 0,
        "crawl_data": {},
        "vulnerabilities": [],
        "attack_paths": [],
        "summary": {},
        "agent_logs": [],
        "report_json": {},
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    result = db.table("url_scans").insert(row).execute()
    return result.data[0] if result.data else row


async def get_url_scan(scan_id: str) -> Optional[Dict[str, Any]]:
    db = get_supabase()
    result = db.table("url_scans").select("*").eq("id", scan_id).execute()
    return result.data[0] if result.data else None


async def update_url_scan(scan_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    db = get_supabase()
    updates["updated_at"] = now_iso()
    result = db.table("url_scans").update(updates).eq("id", scan_id).execute()
    return result.data[0] if result.data else {}


async def list_url_scans(limit: int = 50) -> List[Dict[str, Any]]:
    db = get_supabase()
    result = db.table("url_scans").select("*").order("created_at", desc=True).limit(limit).execute()
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
