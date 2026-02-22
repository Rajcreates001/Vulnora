"""Agent logs API routes."""

import uuid as uuid_mod
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import get_db
from models.db_models import AgentLog
from models.schemas import AgentLogResponse

router = APIRouter()


@router.get("/agent-logs/{candidate_id}", response_model=List[AgentLogResponse])
async def get_agent_logs(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all agent reasoning logs for a candidate."""
    result = await db.execute(
        select(AgentLog)
        .where(AgentLog.candidate_id == uuid_mod.UUID(candidate_id))
        .order_by(AgentLog.timestamp.asc())
    )
    logs = result.scalars().all()
    return logs
