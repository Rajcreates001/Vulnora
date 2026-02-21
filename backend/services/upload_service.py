"""Upload and project management service."""

import os
import tempfile
from typing import Dict, Any

from db.supabase_client import create_project, store_file, update_project
from utils.file_handler import extract_zip, clone_github_repo, collect_files


async def handle_zip_upload(file_content: bytes, filename: str, project_name: str) -> Dict[str, Any]:
    """Handle ZIP file upload: create project, extract, and store files."""
    import time
    start_total = time.time()
    project = await create_project(project_name)
    project_id = project["id"]

    # Save ZIP to temp file
    t0 = time.time()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    tmp.write(file_content)
    tmp.close()
    t1 = time.time()
    print(f"[UPLOAD] Saved ZIP to temp file in {t1-t0:.2f}s")

    # Extract
    t2 = time.time()
    extract_dir = await extract_zip(tmp.name, project_id)
    t3 = time.time()
    print(f"[UPLOAD] Extracted ZIP in {t3-t2:.2f}s")

    # Collect and store files
    t4 = time.time()
    files = collect_files(extract_dir)
    print(f"[UPLOAD] Collected {len(files)} files in {time.time()-t4:.2f}s")
    t5 = time.time()
    import asyncio
    from db.supabase_client import store_agent_log
    async def store_one(f):
        rel_path, content, language = f
        import time
        t0 = time.time()
        try:
            result = await store_file(project_id, rel_path, content, language)
            t1 = time.time()
            if t1-t0 > 1.0:
                await store_agent_log(project_id, "upload", f"Slow file store: {rel_path} ({t1-t0:.2f}s)", log_type="warning")
            return result
        except Exception as e:
            await store_agent_log(project_id, "upload", f"Failed to store file: {rel_path} ({str(e)})", log_type="error")
            print(f"[UPLOAD] ERROR storing {rel_path}: {e}")
            return None
    # Process in batches of 50 for memory safety
    batch_size = 50
    for i in range(0, len(files), batch_size):
        batch = files[i:i+batch_size]
        await asyncio.gather(*(store_one(f) for f in batch))
        print(f"[UPLOAD] Stored {min(i+batch_size, len(files))}/{len(files)} files (batch {i//batch_size+1})")
    t6 = time.time()
    print(f"[UPLOAD] Stored all files in {t6-t5:.2f}s (async batch)")

    await update_project(project_id, {"repo_path": extract_dir})

    print(f"[UPLOAD] Total upload+extract+store time: {time.time()-start_total:.2f}s")

    os.unlink(tmp.name)

    return {
        "project_id": project_id,
        "name": project_name,
        "file_count": len(files),
        "files": [{"path": f[0], "language": f[2]} for f in files],
    }


async def handle_github_upload(repo_url: str, project_name: str) -> Dict[str, Any]:
    """Handle GitHub repo URL: clone, create project, and store files."""
    import time
    start_total = time.time()
    project = await create_project(project_name)
    project_id = project["id"]

    # Clone repository
    t0 = time.time()
    clone_dir = await clone_github_repo(repo_url, project_id)
    t1 = time.time()
    print(f"[UPLOAD] Cloned repo in {t1-t0:.2f}s")

    # Collect and store files
    t2 = time.time()
    files = collect_files(clone_dir)
    print(f"[UPLOAD] Collected {len(files)} files in {time.time()-t2:.2f}s")
    t3 = time.time()
    import asyncio
    from db.supabase_client import store_agent_log
    async def store_one(f):
        rel_path, content, language = f
        import time
        t0 = time.time()
        try:
            result = await store_file(project_id, rel_path, content, language)
            t1 = time.time()
            if t1-t0 > 1.0:
                await store_agent_log(project_id, "upload", f"Slow file store: {rel_path} ({t1-t0:.2f}s)", log_type="warning")
            return result
        except Exception as e:
            await store_agent_log(project_id, "upload", f"Failed to store file: {rel_path} ({str(e)})", log_type="error")
            print(f"[UPLOAD] ERROR storing {rel_path}: {e}")
            return None
    batch_size = 50
    for i in range(0, len(files), batch_size):
        batch = files[i:i+batch_size]
        await asyncio.gather(*(store_one(f) for f in batch))
        print(f"[UPLOAD] Stored {min(i+batch_size, len(files))}/{len(files)} files (batch {i//batch_size+1})")
    t4 = time.time()
    print(f"[UPLOAD] Stored all files in {t4-t3:.2f}s (async batch)")

    await update_project(project_id, {"repo_path": clone_dir})

    print(f"[UPLOAD] Total repo clone+store time: {time.time()-start_total:.2f}s")

    return {
        "project_id": project_id,
        "name": project_name,
        "file_count": len(files),
        "files": [{"path": f[0], "language": f[2]} for f in files],
    }
