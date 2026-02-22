"""Interview service — manages live interview sessions with timer enforcement."""

import logging
import uuid as uuid_mod
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.db_models import Candidate, Evaluation, AgentLog
from agents.interview_agent import interview_agent
from services.evaluation import evaluation_service, _safe_score

logger = logging.getLogger(__name__)

# In-memory interview sessions (use Redis for production)
_active_sessions: Dict[str, "InterviewSession"] = {}


class InterviewSession:
    """Manages a single interview session with timer and question tracking."""

    def __init__(self, candidate_id: str, job_description: str, resume_text: str, duration_minutes: int = 15, in_person_transcript: str = ""):
        self.session_id = str(uuid_mod.uuid4())
        self.candidate_id = candidate_id
        self.job_description = job_description
        self.resume_text = resume_text
        self.duration_minutes = duration_minutes
        self.in_person_transcript = in_person_transcript
        self.transcript: List[Dict[str, Any]] = []
        self.questions: List[Dict[str, Any]] = []
        self.questions_asked_texts: List[str] = []  # Track question texts to prevent repeats
        self.current_question_index = 0
        self.answer_assessments: List[Dict[str, Any]] = []
        self.emotion_timeline: List[Dict[str, Any]] = []  # Per-answer emotion snapshots
        self.started_at: Optional[datetime] = None
        self.ended_at: Optional[datetime] = None
        self.status = "pending"  # pending, active, completed, cancelled, time_expired

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time since interview started."""
        if not self.started_at:
            return 0
        end = self.ended_at or datetime.now(timezone.utc)
        return (end - self.started_at).total_seconds()

    @property
    def remaining_seconds(self) -> float:
        """Get remaining time in the interview."""
        return max(0, self.duration_minutes * 60 - self.elapsed_seconds)

    @property
    def is_time_expired(self) -> bool:
        """Check if interview time has expired."""
        return self.elapsed_seconds >= self.duration_minutes * 60

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "candidate_id": self.candidate_id,
            "status": self.status,
            "duration_minutes": self.duration_minutes,
            "current_question_index": self.current_question_index,
            "total_questions": len(self.questions),
            "transcript_length": len(self.transcript),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "elapsed_seconds": self.elapsed_seconds,
            "remaining_seconds": self.remaining_seconds,
            "is_time_expired": self.is_time_expired,
        }


class InterviewService:
    """Orchestrates live interview sessions with timer enforcement."""

    async def start_session(
        self, candidate_id: str, db: AsyncSession, duration_minutes: int = 15,
        in_person_transcript: str = None,
    ) -> Dict[str, Any]:
        """Initialize a new interview session for a candidate."""
        result = await db.execute(
            select(Candidate).where(Candidate.id == uuid_mod.UUID(candidate_id))
        )
        candidate = result.scalar_one_or_none()
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")

        logger.info(f"[InterviewService] Starting session for candidate {candidate_id}, duration={duration_minutes}min")

        # Generate initial questions — include in-person transcript for context
        questions = await interview_agent.generate_opening_questions(
            candidate.job_description,
            candidate.resume_text,
            num_questions=5,
            in_person_transcript=in_person_transcript or "",
        )

        # Create session
        session = InterviewSession(
            candidate_id=candidate_id,
            job_description=candidate.job_description,
            resume_text=candidate.resume_text,
            duration_minutes=duration_minutes,
            in_person_transcript=in_person_transcript or "",
        )
        session.questions = questions
        session.started_at = datetime.now(timezone.utc)
        session.status = "active"

        # Track question texts
        for q in questions:
            session.questions_asked_texts.append(q.get("text", ""))

        # Store session
        _active_sessions[session.session_id] = session

        # Update candidate status
        candidate.status = "interviewing"
        await db.flush()
        await db.commit()

        first_question = questions[0] if questions else {
            "text": "Hey there! Welcome to the interview — I'm your AI interviewer today. Go ahead and introduce yourself! Tell me a bit about who you are and what you've been up to.",
            "category": "behavioral",
            "difficulty": "easy",
        }

        # Add AI question to transcript
        session.transcript.append({
            "speaker": "AI Interviewer",
            "text": first_question.get("text", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "question",
            "question_index": 0,
        })

        logger.info(f"[InterviewService] Session {session.session_id} started, {len(questions)} questions generated")

        return {
            "session_id": session.session_id,
            "candidate_id": candidate_id,
            "status": "active",
            "duration_minutes": duration_minutes,
            "current_question": first_question,
            "total_questions": len(questions),
            "started_at": session.started_at.isoformat(),
            "remaining_seconds": session.remaining_seconds,
        }

    async def submit_answer(
        self, session_id: str, answer_text: str, emotion_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Process a candidate's answer and generate follow-up."""
        session = _active_sessions.get(session_id)
        if not session:
            raise ValueError("Interview session not found")
        if session.status != "active":
            raise ValueError(f"Session is {session.status}, not active")

        # Timer enforcement — check if time has expired
        if session.is_time_expired:
            logger.info(f"[InterviewService] Time expired for session {session_id}")
            session.status = "time_expired"
            return {
                "session_id": session_id,
                "next_question": None,
                "answer_assessment": {
                    "quality": "not_assessed",
                    "score": 0,
                    "note": "Interview time has expired."
                },
                "current_question_index": session.current_question_index,
                "total_questions_asked": len(session.questions),
                "transcript_length": len(session.transcript),
                "time_expired": True,
                "remaining_seconds": 0,
            }

        # Add answer to transcript
        session.transcript.append({
            "speaker": "Candidate",
            "text": answer_text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "answer",
            "question_index": session.current_question_index,
            "emotion_data": emotion_data,
        })

        # Store emotion snapshot in timeline
        if emotion_data:
            session.emotion_timeline.append({
                "question_index": session.current_question_index,
                "emotion": emotion_data,
            })

        current_q = (
            session.questions[session.current_question_index]
            if session.current_question_index < len(session.questions)
            else {}
        )

        # Generate follow-up question and assess the answer
        follow_up_data = await interview_agent.generate_follow_up(
            session.job_description,
            session.resume_text,
            session.transcript,
            answer_text,
            current_q,
            questions_asked=session.questions_asked_texts,
            in_person_transcript=session.in_person_transcript,
            emotion_data=emotion_data,
        )

        # Store assessment
        assessment = follow_up_data.get("answer_assessment", {})
        session.answer_assessments.append({
            "question_index": session.current_question_index,
            "assessment": assessment,
        })

        # Extract agent reply (reaction to the answer)
        reply_data = follow_up_data.get("reply", {})
        reply_text = reply_data.get("text", "") if isinstance(reply_data, dict) else ""
        reply_category = reply_data.get("category", current_q.get("category", "general")) if isinstance(reply_data, dict) else current_q.get("category", "general")

        # Add agent reply to transcript
        if reply_text:
            session.transcript.append({
                "speaker": "AI Interviewer",
                "text": reply_text,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "reply",
                "question_index": session.current_question_index,
                "category": reply_category,
            })

        # Move to next question
        session.current_question_index += 1
        next_question = follow_up_data.get("question", {})

        # Check timer again — if very little time left, signal it
        remaining = session.remaining_seconds
        if remaining <= 0:
            session.status = "time_expired"
            return {
                "session_id": session_id,
                "reply": {"text": reply_text, "category": reply_category} if reply_text else None,
                "next_question": None,
                "answer_assessment": assessment,
                "current_question_index": session.current_question_index,
                "total_questions_asked": len(session.questions),
                "transcript_length": len(session.transcript),
                "time_expired": True,
                "remaining_seconds": 0,
            }

        # Add to questions list and transcript
        if next_question and next_question.get("text"):
            session.questions.append(next_question)
            session.questions_asked_texts.append(next_question.get("text", ""))
            session.transcript.append({
                "speaker": "AI Interviewer",
                "text": next_question.get("text", ""),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "question",
                "question_index": session.current_question_index,
            })

        return {
            "session_id": session_id,
            "reply": {"text": reply_text, "category": reply_category} if reply_text else None,
            "next_question": next_question,
            "answer_assessment": assessment,
            "current_question_index": session.current_question_index,
            "total_questions_asked": len(session.questions),
            "transcript_length": len(session.transcript),
            "time_expired": False,
            "remaining_seconds": remaining,
        }

    async def end_session(
        self, session_id: str, db: AsyncSession
    ) -> Dict[str, Any]:
        """End the interview and trigger full evaluation."""
        session = _active_sessions.get(session_id)
        if not session:
            raise ValueError("Interview session not found")

        session.status = "completed"
        session.ended_at = datetime.now(timezone.utc)

        # Build transcript text for evaluation
        transcript_text = self._build_transcript_text(session)

        # Update candidate with interview transcript
        result = await db.execute(
            select(Candidate).where(Candidate.id == uuid_mod.UUID(session.candidate_id))
        )
        candidate = result.scalar_one_or_none()
        if candidate:
            candidate.transcript_text = transcript_text
            candidate.status = "pending"  # Ready for evaluation
            await db.flush()
            await db.commit()

        # Get interview-specific evaluation
        interview_eval = await interview_agent.evaluate_full_interview(
            session.job_description,
            session.resume_text,
            session.transcript,
        )

        return {
            "session_id": session_id,
            "candidate_id": session.candidate_id,
            "status": "completed",
            "duration_seconds": (
                (session.ended_at - session.started_at).total_seconds()
                if session.started_at and session.ended_at
                else 0
            ),
            "total_questions": len(session.questions),
            "transcript": session.transcript,
            "transcript_text": transcript_text,
            "interview_evaluation": interview_eval,
            "answer_assessments": session.answer_assessments,
        }

    async def end_and_evaluate_stream(
        self, session_id: str, db: AsyncSession
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """End interview and stream the evaluation pipeline."""
        session = _active_sessions.get(session_id)
        if not session:
            yield {"type": "error", "message": "Interview session not found"}
            return

        session.status = "completed"
        session.ended_at = datetime.now(timezone.utc)

        elapsed = session.elapsed_seconds
        logger.info(f"[InterviewService] Ending session {session_id}, elapsed={elapsed:.0f}s, questions={len(session.questions)}")

        yield {
            "type": "status",
            "message": f"Interview completed ({len(session.questions)} questions, {int(elapsed)}s). Generating transcript...",
            "phase": "transcript",
        }

        transcript_text = self._build_transcript_text(session)

        # Update candidate
        result = await db.execute(
            select(Candidate).where(Candidate.id == uuid_mod.UUID(session.candidate_id))
        )
        candidate = result.scalar_one_or_none()
        if candidate:
            candidate.transcript_text = transcript_text
            candidate.status = "pending"
            await db.flush()
            await db.commit()

        yield {
            "type": "transcript_ready",
            "transcript": session.transcript,
            "transcript_text": transcript_text,
            "total_questions": len(session.questions),
        }

        yield {
            "type": "status",
            "message": "Starting AI evaluation pipeline...",
            "phase": "evaluation",
        }

        # Now run the full evaluation pipeline via SSE
        async for event in evaluation_service.run_evaluation_stream(session.candidate_id, db):
            yield event

        # Clean up
        if session_id in _active_sessions:
            del _active_sessions[session_id]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session state."""
        session = _active_sessions.get(session_id)
        if not session:
            return None
        return {
            **session.to_dict(),
            "transcript": session.transcript,
            "questions": session.questions,
            "answer_assessments": session.answer_assessments,
        }

    def get_transcript(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get session transcript."""
        session = _active_sessions.get(session_id)
        return session.transcript if session else None

    def _build_transcript_text(self, session: InterviewSession) -> str:
        """Convert session transcript to formatted text with question numbers and emotion data."""
        lines = []
        q_num = 0
        for entry in session.transcript:
            ts = entry.get("timestamp", "")
            speaker = entry.get("speaker", "Unknown")
            text = entry.get("text", "")
            if speaker == "AI Interviewer":
                q_num += 1
                lines.append(f"[{ts}] AI Interviewer (Q{q_num}): {text}")
            else:
                emotion_str = ""
                ed = entry.get("emotion_data")
                if ed and isinstance(ed, dict):
                    dom = ed.get("dominant", "unknown")
                    eng = ed.get("engagement", 0)
                    stress = ed.get("stress", 0)
                    pos = ed.get("positivity", 0)
                    emotion_str = f" [Emotion: {dom} | Engagement: {eng}% | Stress: {stress}% | Positivity: {pos}%]"
                lines.append(f"[{ts}] Candidate (A{q_num}): {text}{emotion_str}")
        
        # Add interview metadata at the top
        duration_str = f"{int(session.elapsed_seconds)}s" if session.started_at else "unknown"
        header = f"--- Interview Transcript ---\nDuration: {duration_str}\nQuestions Asked: {q_num}\n"
        
        # Include in-person transcript if available
        if session.in_person_transcript:
            header += f"\n--- In-Person Interview Transcript (provided) ---\n{session.in_person_transcript}\n--- End In-Person Transcript ---\n"
        
        # Include emotion summary
        if session.emotion_timeline:
            avg_engagement = sum(e["emotion"].get("engagement", 0) for e in session.emotion_timeline) / len(session.emotion_timeline)
            avg_stress = sum(e["emotion"].get("stress", 0) for e in session.emotion_timeline) / len(session.emotion_timeline)
            avg_positivity = sum(e["emotion"].get("positivity", 0) for e in session.emotion_timeline) / len(session.emotion_timeline)
            header += f"\n--- Emotion Analysis Summary ---\n"
            header += f"Average Engagement: {avg_engagement:.0f}%\n"
            header += f"Average Stress: {avg_stress:.0f}%\n"
            header += f"Average Positivity: {avg_positivity:.0f}%\n"
            header += f"--- End Emotion Summary ---\n"
        
        header += "---\n\n"
        return header + "\n\n".join(lines)


# Singleton
interview_service = InterviewService()
