"""Candidate management API routes."""

import uuid as uuid_mod
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from PyPDF2 import PdfReader
import io

from db.database import get_db
from models.db_models import Candidate
from models.schemas import CandidateCreate, CandidateResponse, CandidateDetail

router = APIRouter()


@router.post("/upload-candidate", response_model=CandidateResponse)
async def upload_candidate(
    candidate: CandidateCreate,
    db: AsyncSession = Depends(get_db),
):
    """Upload a new candidate with resume, transcript, and job description."""
    new_candidate = Candidate(
        name=candidate.name,
        email=candidate.email,
        resume_text=candidate.resume_text,
        transcript_text=candidate.transcript_text or "",
        job_description=candidate.job_description,
        status="pending",
    )
    db.add(new_candidate)
    await db.flush()
    await db.refresh(new_candidate)
    return new_candidate


@router.post("/upload-candidate-files", response_model=CandidateResponse)
async def upload_candidate_files(
    name: str = Form(...),
    email: str = Form(None),
    job_description: str = Form(...),
    resume: UploadFile = File(...),
    transcript: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
):
    """Upload candidate with PDF/DOCX/text files."""
    resume_text = await _extract_text(resume)
    transcript_text = ""
    if transcript:
        transcript_text = await _extract_text(transcript)

    new_candidate = Candidate(
        name=name,
        email=email,
        resume_text=resume_text,
        transcript_text=transcript_text,
        job_description=job_description,
        status="pending",
    )
    db.add(new_candidate)
    await db.flush()
    await db.refresh(new_candidate)
    return new_candidate


@router.get("/candidates", response_model=List[CandidateResponse])
async def list_candidates(
    db: AsyncSession = Depends(get_db),
):
    """List all candidates."""
    result = await db.execute(
        select(Candidate).order_by(Candidate.created_at.desc())
    )
    return result.scalars().all()


@router.get("/candidates/{candidate_id}", response_model=CandidateDetail)
async def get_candidate(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific candidate with full details."""
    result = await db.execute(
        select(Candidate).where(Candidate.id == uuid_mod.UUID(candidate_id))
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.delete("/candidates/{candidate_id}")
async def delete_candidate(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a candidate and all associated data."""
    result = await db.execute(
        select(Candidate).where(Candidate.id == uuid_mod.UUID(candidate_id))
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    await db.delete(candidate)
    return {"status": "deleted", "candidate_id": candidate_id}


@router.patch("/candidates/{candidate_id}/reset")
async def reset_candidate_status(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Reset candidate status to pending (useful for re-evaluation)."""
    result = await db.execute(
        select(Candidate).where(Candidate.id == uuid_mod.UUID(candidate_id))
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    candidate.status = "pending"
    await db.flush()
    return {"status": "reset", "candidate_id": candidate_id}


async def _extract_text(file: UploadFile) -> str:
    """Extract text from an uploaded file (PDF, DOCX, or plain text)."""
    content = await file.read()
    filename = (file.filename or "").lower()

    if filename.endswith(".pdf"):
        try:
            reader = PdfReader(io.BytesIO(content))
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text.strip()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {str(e)}")

    elif filename.endswith(".docx"):
        try:
            from docx import Document
            doc = Document(io.BytesIO(content))
            text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            return text.strip()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse DOCX: {str(e)}")

    else:
        return content.decode("utf-8", errors="ignore").strip()

