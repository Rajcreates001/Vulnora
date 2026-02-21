"""File handling utilities for repository upload and extraction."""

import os
import shutil
import zipfile
import tempfile
from typing import List, Tuple
from pathlib import Path

import httpx

from config import settings


SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".rb",
    ".php", ".c", ".cpp", ".h", ".cs", ".sql", ".html", ".css",
    ".yml", ".yaml", ".json", ".xml", ".sh", ".env", ".md",
    ".txt", ".cfg", ".ini", ".toml", ".lock",
}

IGNORED_DIRS = {
    "node_modules", ".git", "__pycache__", ".next", "dist", "build",
    ".venv", "venv", "env", ".idea", ".vscode", ".cache", "coverage",
    ".tox", "egg-info",
}

MAX_FILE_SIZE = 500_000  # 500KB per file


def ensure_upload_dir() -> str:
    upload_dir = settings.upload_dir
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


async def extract_zip(zip_path: str, project_id: str) -> str:
    """Extract ZIP file and return the extraction directory."""
    extract_dir = os.path.join(ensure_upload_dir(), project_id)
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)
    return extract_dir


async def clone_github_repo(repo_url: str, project_id: str) -> str:
    """Clone a GitHub repository (public or with token). Falls back to ZIP download if git unavailable."""
    clone_dir = os.path.join(ensure_upload_dir(), project_id)
    os.makedirs(clone_dir, exist_ok=True)

    # Method 1: Try using gitpython
    try:
        import git

        auth_url = repo_url
        if settings.github_token and "github.com" in repo_url:
            auth_url = repo_url.replace(
                "https://github.com",
                f"https://{settings.github_token}@github.com",
            )

        git.Repo.clone_from(auth_url, clone_dir, depth=1)
        return clone_dir
    except ImportError:
        pass  # GitPython not installed, try fallback
    except Exception:
        # Git clone failed, clean up and try fallback
        shutil.rmtree(clone_dir, ignore_errors=True)
        os.makedirs(clone_dir, exist_ok=True)

    # Method 2: Download ZIP archive via GitHub API
    try:
        # Convert URL to ZIP download URL
        # https://github.com/user/repo → https://github.com/user/repo/archive/refs/heads/main.zip
        clean_url = repo_url.rstrip("/").rstrip(".git")
        zip_url = f"{clean_url}/archive/refs/heads/main.zip"

        headers = {}
        if settings.github_token:
            headers["Authorization"] = f"token {settings.github_token}"

        async with httpx.AsyncClient(follow_redirects=True, timeout=120.0) as client:
            response = await client.get(zip_url, headers=headers)

            if response.status_code == 404:
                # Try 'master' branch
                zip_url = f"{clean_url}/archive/refs/heads/master.zip"
                response = await client.get(zip_url, headers=headers)

            if response.status_code != 200:
                raise Exception(f"GitHub download failed with status {response.status_code}")

            # Save ZIP and extract
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
            tmp.write(response.content)
            tmp.close()

            try:
                with zipfile.ZipFile(tmp.name, "r") as zf:
                    zf.extractall(clone_dir)

                # GitHub ZIP archives have a top-level directory (repo-main/)
                # Move contents up one level
                subdirs = [d for d in Path(clone_dir).iterdir() if d.is_dir()]
                if len(subdirs) == 1:
                    inner_dir = subdirs[0]
                    for item in inner_dir.iterdir():
                        dest = Path(clone_dir) / item.name
                        if dest.exists():
                            if dest.is_dir():
                                shutil.rmtree(dest)
                            else:
                                dest.unlink()
                        shutil.move(str(item), str(dest))
                    inner_dir.rmdir()
            finally:
                os.unlink(tmp.name)

        return clone_dir
    except Exception as e:
        raise Exception(f"Failed to clone repository: {str(e)}")


def collect_files(directory: str) -> List[Tuple[str, str, str]]:
    """Collect all supported files from a directory.
    
    Returns: List of (relative_path, content, language)
    """
    files = []
    base = Path(directory)

    for root, dirs, filenames in os.walk(directory):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        for filename in filenames:
            filepath = Path(root) / filename
            ext = filepath.suffix.lower()

            if ext not in SUPPORTED_EXTENSIONS:
                continue

            if filepath.stat().st_size > MAX_FILE_SIZE:
                continue

            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
                relative_path = str(filepath.relative_to(base)).replace("\\", "/")
                language = _detect_lang(ext)
                files.append((relative_path, content, language))
            except Exception:
                continue

    return files


def _detect_lang(ext: str) -> str:
    mapping = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".tsx": "typescript", ".jsx": "javascript", ".java": "java",
        ".go": "go", ".rs": "rust", ".rb": "ruby", ".php": "php",
        ".c": "c", ".cpp": "cpp", ".h": "c", ".cs": "csharp",
        ".sql": "sql", ".html": "html", ".css": "css",
        ".yml": "yaml", ".yaml": "yaml", ".json": "json",
    }
    return mapping.get(ext, "unknown")


def cleanup_project_files(project_id: str) -> None:
    """Clean up uploaded project files."""
    project_dir = os.path.join(settings.upload_dir, project_id)
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir, ignore_errors=True)
