"""Project and upload API routes."""


from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from typing import Optional
from utils import verify_jwt_token, verify_api_key

from services.upload_service import handle_zip_upload, handle_github_upload
from db.supabase_client import get_projects, get_project, get_project_files
from models.schemas import APIResponse

router = APIRouter(prefix="/api", tags=["projects"])


@router.post("/upload-repo")
async def upload_repo(
    file: Optional[UploadFile] = File(None),
    repo_url: Optional[str] = Form(None),
    project_name: str = Form(...),
    jwt_payload: dict = Depends(verify_jwt_token),
    api_key_ok: bool = Depends(verify_api_key),
):
    """Upload a ZIP repository or provide a GitHub URL."""
    try:
        if file and file.filename:
            if not file.filename.endswith(".zip"):
                raise HTTPException(status_code=400, detail="Only ZIP files are supported")
            content = await file.read()
            result = await handle_zip_upload(content, file.filename, project_name)
            return APIResponse(success=True, data=result)

        elif repo_url:
            if not repo_url.startswith("https://github.com"):
                raise HTTPException(status_code=400, detail="Only GitHub URLs are supported")
            result = await handle_github_upload(repo_url, project_name)
            return APIResponse(success=True, data=result)

        else:
            raise HTTPException(status_code=400, detail="Provide either a ZIP file or GitHub URL")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects")
async def list_projects(
    jwt_payload: dict = Depends(verify_jwt_token),
    api_key_ok: bool = Depends(verify_api_key),
):
    """List all projects."""
    projects = await get_projects()
    return APIResponse(success=True, data={"projects": projects, "total": len(projects)})


@router.get("/projects/{project_id}")
async def get_project_detail(
    project_id: str,
    jwt_payload: dict = Depends(verify_jwt_token),
    api_key_ok: bool = Depends(verify_api_key),
):
    """Get project details."""
    project = await get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    files = await get_project_files(project_id)
    project["file_count"] = len(files)
    project["files"] = [
        {"id": f["id"], "file_path": f["file_path"], "language": f.get("language", "unknown"), "size": f.get("size", 0)}
        for f in files
    ]
    return APIResponse(success=True, data=project)


@router.get("/files/{file_id}")
async def get_file(
    file_id: str,
    jwt_payload: dict = Depends(verify_jwt_token),
    api_key_ok: bool = Depends(verify_api_key),
):
    """Get file content."""
    from db.supabase_client import get_file_content
    file_data = await get_file_content(file_id)
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")
    return APIResponse(success=True, data=file_data)
