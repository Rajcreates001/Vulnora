"""Evaluation API routes."""

import uuid as uuid_mod
import json as json_module
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import get_db, async_session
from models.db_models import Evaluation, Candidate
from models.schemas import EvaluationResponse, RunEvaluationRequest, EvaluationSummary
from services.evaluation import evaluation_service

router = APIRouter()


@router.get("/run-evaluation-stream/{candidate_id}")
async def run_evaluation_stream(candidate_id: str):
    """Stream evaluation progress via Server-Sent Events."""

    async def event_generator():
        async with async_session() as db:
            try:
                async for event in evaluation_service.run_evaluation_stream(candidate_id, db):
                    yield f"data: {json_module.dumps(event)}\n\n"
                # Commit is already handled inside run_evaluation_stream after _save_evaluation
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


@router.post("/run-evaluation")
async def run_evaluation(
    request: RunEvaluationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Trigger the full multi-agent evaluation pipeline for a candidate."""
    candidate_id = str(request.candidate_id)

    # Verify candidate exists
    result = await db.execute(
        select(Candidate).where(Candidate.id == uuid_mod.UUID(candidate_id))
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    if candidate.status == "evaluating":
        raise HTTPException(status_code=409, detail="Evaluation already in progress")

    # Run evaluation
    try:
        eval_result = await evaluation_service.run_evaluation(candidate_id, db)
        return eval_result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {str(e)}"
        )


@router.get("/evaluation-results/{candidate_id}", response_model=EvaluationResponse)
async def get_evaluation_results(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get evaluation results for a candidate."""
    result = await db.execute(
        select(Evaluation)
        .where(Evaluation.candidate_id == uuid_mod.UUID(candidate_id))
        .order_by(Evaluation.created_at.desc())
    )
    evaluation = result.scalar_one_or_none()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return evaluation


@router.get("/evaluations", response_model=List[EvaluationSummary])
async def list_evaluations(
    db: AsyncSession = Depends(get_db),
):
    """List all evaluations with summary data."""
    result = await db.execute(
        select(Evaluation, Candidate.name)
        .join(Candidate, Candidate.id == Evaluation.candidate_id)
        .order_by(Evaluation.created_at.desc())
    )
    rows = result.all()

    summaries = []
    for eval_obj, candidate_name in rows:
        summaries.append(EvaluationSummary(
            candidate_id=eval_obj.candidate_id,
            candidate_name=candidate_name,
            final_decision=eval_obj.final_decision,
            confidence=eval_obj.confidence,
            technical_score=eval_obj.technical_score,
            risk_score=eval_obj.risk_score,
            created_at=eval_obj.created_at,
        ))
    return summaries
