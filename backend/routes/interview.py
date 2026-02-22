"""Interview API routes — manage live interview sessions."""

import json as json_module
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db, async_session
from services.interview import interview_service
from agents.interview_agent import interview_agent

router = APIRouter()


class StartInterviewRequest(BaseModel):
    candidate_id: str
    duration_minutes: int = 15
    in_person_transcript: Optional[str] = None


class SubmitAnswerRequest(BaseModel):
    session_id: str
    answer_text: str
    emotion_data: Optional[dict] = None


class ExtractResumeRequest(BaseModel):
    resume_text: str


@router.post("/interview/start")
async def start_interview(
    request: StartInterviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """Start a new live interview session."""
    try:
        result = await interview_service.start_session(
            request.candidate_id, db, request.duration_minutes,
            in_person_transcript=request.in_person_transcript,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")


@router.post("/interview/answer")
async def submit_answer(request: SubmitAnswerRequest):
    """Submit candidate's answer and get follow-up question."""
    try:
        result = await interview_service.submit_answer(
            request.session_id, request.answer_text,
            emotion_data=request.emotion_data,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process answer: {str(e)}")


@router.post("/interview/end/{session_id}")
async def end_interview(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """End the interview and get evaluation."""
    try:
        result = await interview_service.end_session(session_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to end interview: {str(e)}")


@router.get("/interview/end-and-evaluate/{session_id}")
async def end_and_evaluate_stream(session_id: str):
    """End interview and stream the full evaluation via SSE."""

    async def event_generator():
        async with async_session() as db:
            try:
                async for event in interview_service.end_and_evaluate_stream(session_id, db):
                    yield f"data: {json_module.dumps(event)}\n\n"
            except Exception as e:
                await db.rollback()
                yield f"data: {json_module.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/interview/session/{session_id}")
async def get_session(session_id: str):
    """Get current interview session state."""
    session = interview_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/interview/transcript/{session_id}")
async def get_transcript(session_id: str):
    """Get interview transcript."""
    transcript = interview_service.get_transcript(session_id)
    if transcript is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"transcript": transcript}


@router.post("/resume/extract")
async def extract_resume_data(request: ExtractResumeRequest):
    """Extract structured data from resume text using AI."""
    try:
        data = await interview_agent.extract_resume_data(request.resume_text)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume extraction failed: {str(e)}")
