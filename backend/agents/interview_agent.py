"""Interview Agent — Generates dynamic questions and analyzes responses in real-time.

Key improvements:
- Robust error handling with detailed logging (no silent failures)
- Retry logic for OpenAI API calls
- Smart adaptive questioning that handles uncooperative candidates
- Conversation context tracking to prevent question repetition
- Gibberish/nonsense detection
- Difficulty adaptation based on answer quality
- Multiple question strategies for different candidate types
"""

import json
import logging
import asyncio
from typing import Any, Dict, List, Optional
from openai import AsyncOpenAI
from config import get_settings

logger = logging.getLogger(__name__)

# ── Helpers ──────────────────────────────────────────────────────────────

def _is_gibberish(text: str) -> bool:
    """Detect if text is gibberish/nonsensical."""
    text = text.strip().lower()
    if len(text) < 3:
        return True
    alpha_chars = sum(1 for c in text if c.isalpha())
    if alpha_chars < len(text) * 0.4:
        return True
    vowels = sum(1 for c in text if c in 'aeiou')
    consonants = sum(1 for c in text if c.isalpha() and c not in 'aeiou')
    if consonants > 0 and vowels == 0 and len(text) > 5:
        return True
    non_answers = [
        "i don't know", "i dont know", "no idea", "nothing", "pass",
        "skip", "next", "whatever", "idk", "dunno", "no",
        "about??", "about", "how", "what", "why", "huh", "um",
    ]
    if text in non_answers:
        return True
    return False


def _answer_quality(text: str) -> str:
    """Quick heuristic classification of answer quality."""
    text = text.strip()
    if _is_gibberish(text):
        return "gibberish"
    word_count = len(text.split())
    if word_count <= 3:
        return "very_short"
    if word_count <= 10:
        return "short"
    if word_count <= 30:
        return "adequate"
    return "detailed"


# Pool of diverse fallback questions by category
_FALLBACK_QUESTION_POOLS: Dict[str, List[Dict[str, Any]]] = {
    "technical": [
        {"text": "Can you walk me through a technical project you built from scratch? What were the core design decisions?", "category": "technical", "difficulty": "medium", "evaluating": "System design and architecture thinking"},
        {"text": "What programming languages and frameworks are you most comfortable with, and why?", "category": "technical", "difficulty": "easy", "evaluating": "Technical skill awareness"},
        {"text": "Describe a debugging challenge you faced. How did you identify and fix the root cause?", "category": "technical", "difficulty": "medium", "evaluating": "Problem-solving methodology"},
        {"text": "How do you decide between different technology choices when starting a new project?", "category": "technical", "difficulty": "medium", "evaluating": "Technical decision-making"},
        {"text": "Can you explain the difference between a relational database and a NoSQL database, and when you'd use each?", "category": "technical", "difficulty": "easy", "evaluating": "Database fundamentals"},
    ],
    "behavioral": [
        {"text": "Tell me about a time you had a disagreement with a teammate. How did you resolve it?", "category": "behavioral", "difficulty": "medium", "evaluating": "Conflict resolution and teamwork"},
        {"text": "Describe a situation where you failed at something. What did you learn from it?", "category": "behavioral", "difficulty": "medium", "evaluating": "Self-awareness and growth mindset"},
        {"text": "How do you handle tight deadlines when you have multiple priorities?", "category": "behavioral", "difficulty": "easy", "evaluating": "Time management and prioritization"},
        {"text": "Tell me about a time you had to learn something new quickly for a project.", "category": "behavioral", "difficulty": "easy", "evaluating": "Learning agility"},
        {"text": "How do you communicate technical concepts to non-technical stakeholders?", "category": "behavioral", "difficulty": "medium", "evaluating": "Communication skills"},
    ],
    "domain": [
        {"text": "What industry trends or technologies excite you the most right now?", "category": "domain", "difficulty": "easy", "evaluating": "Industry awareness"},
        {"text": "How do you stay current with developments in your field?", "category": "domain", "difficulty": "easy", "evaluating": "Continuous learning habits"},
        {"text": "What do you think are the biggest challenges in this domain right now?", "category": "domain", "difficulty": "medium", "evaluating": "Domain insight"},
    ],
    "problem_solving": [
        {"text": "If you were given a completely unfamiliar codebase and asked to add a feature, how would you approach it?", "category": "problem_solving", "difficulty": "medium", "evaluating": "Analytical approach to unknowns"},
        {"text": "How would you approach optimizing a slow-running application?", "category": "problem_solving", "difficulty": "medium", "evaluating": "Performance analysis thinking"},
        {"text": "Describe your process for breaking down a complex problem into smaller parts.", "category": "problem_solving", "difficulty": "easy", "evaluating": "Decomposition skills"},
    ],
    "experience_validation": [
        {"text": "Can you walk me through your most recent project and your specific role in it?", "category": "experience_validation", "difficulty": "easy", "evaluating": "Resume claim verification"},
        {"text": "What was the most impactful contribution you made in your last role?", "category": "experience_validation", "difficulty": "medium", "evaluating": "Impact and ownership"},
    ],
}


class InterviewAgent:
    """AI Interview Agent that generates questions and evaluates answers dynamically."""

    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        self.model = self.settings.llm_model

    async def _call_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.4,
        retries: int = 2,
    ) -> Optional[Dict[str, Any]]:
        """Call OpenAI with retry logic and detailed error logging."""
        last_error = None
        content = ""
        for attempt in range(retries + 1):
            try:
                logger.info(f"[InterviewAgent] OpenAI call attempt {attempt + 1}/{retries + 1}, model={self.model}")
                response = await self.client.chat.completions.create(
                    model=self.model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content or "{}"
                logger.info(f"[InterviewAgent] Response received, length={len(content)}")
                data = json.loads(content)
                return data
            except json.JSONDecodeError as e:
                logger.error(f"[InterviewAgent] JSON parse error attempt {attempt + 1}: {e}")
                logger.error(f"[InterviewAgent] Raw content: {content[:1000]}")
                last_error = e
            except Exception as e:
                logger.error(f"[InterviewAgent] API error attempt {attempt + 1}: {type(e).__name__}: {e}", exc_info=True)
                last_error = e
                if attempt < retries:
                    wait = 1.5 * (attempt + 1)
                    logger.info(f"[InterviewAgent] Retrying in {wait}s...")
                    await asyncio.sleep(wait)

        logger.error(f"[InterviewAgent] All {retries + 1} attempts failed. Last error: {last_error}")
        return None

    def _get_fallback_question(self, category: str, asked_texts: List[str]) -> Dict[str, Any]:
        """Get a fallback question that hasn't been asked yet."""
        categories_to_try = [category] + [c for c in _FALLBACK_QUESTION_POOLS if c != category]
        for cat in categories_to_try:
            pool = _FALLBACK_QUESTION_POOLS.get(cat, [])
            for q in pool:
                if q["text"] not in asked_texts:
                    return q
        return {
            "text": "Is there anything else about your background or skills that you'd like to share?",
            "category": "general",
            "difficulty": "easy",
            "evaluating": "Self-presentation",
        }

    async def generate_opening_questions(
        self, job_description: str, resume_text: str, num_questions: int = 5,
        in_person_transcript: str = "",
    ) -> List[Dict[str, Any]]:
        """Generate a warm greeting + interview questions based on JD and resume."""
        transcript_context = ""
        if in_person_transcript and in_person_transcript.strip():
            transcript_context = f"""
## In-Person Interview Transcript (from a previous round)
{in_person_transcript[:3000]}

IMPORTANT: The candidate has already done an in-person interview. Review the transcript above carefully.
- Do NOT ask questions that were already asked/answered in the in-person interview
- DO ask follow-up questions that probe deeper into topics mentioned but not fully explored
- DO ask about inconsistencies or gaps you notice between the transcript and resume
- Reference specific things from the in-person interview to show you've reviewed it
"""

        prompt = f"""You are a friendly, senior interviewer starting a LIVE voice interview. Generate a warm opening greeting followed by {num_questions - 1} interview questions.

## Job Description
{job_description}

## Candidate Resume  
{resume_text}
{transcript_context}
CRITICAL RULES:
- Q1 MUST be a warm, conversational greeting. Example: "Hey! Welcome to the interview. I'm your AI interviewer today. Go ahead and introduce yourself — tell me a bit about who you are and what you've been working on lately."
- The greeting should feel HUMAN — casual, warm, encouraging. NOT robotic.
- Q2-Q{num_questions}: Specific questions about their resume and the job description
- Questions should flow naturally as a conversation, not like a quiz

Required mix:
- Q1: Warm greeting + invitation to introduce themselves (category: "behavioral")
- Q2: Follow-up about their most relevant experience (reference resume)
- Q3: Technical depth question targeting a key JD skill
- Q4: Problem-solving scenario relevant to the role
- Q5: Experience validation question probing a specific resume claim

Respond in JSON:
{{
    "questions": [
        {{
            "id": 1,
            "text": "Hey! Welcome — I'm your AI interviewer today. Before we dive in, go ahead and introduce yourself. Tell me a bit about who you are and what you've been working on.",
            "category": "behavioral",
            "difficulty": "easy",
            "evaluating": "Self-introduction and communication",
            "key_points": ["background", "recent work"],
            "follow_up_topics": ["projects", "role"]
        }}
    ]
}}"""

        data = await self._call_openai(
            system_prompt="You are a warm, friendly expert interviewer who sounds HUMAN — like a real person having a conversation.  Generate natural, conversational questions. The first question MUST be a greeting asking the candidate to introduce themselves.",
            user_prompt=prompt,
            max_tokens=4096,
            temperature=0.5,
        )

        if data and data.get("questions") and len(data["questions"]) > 0:
            logger.info(f"[InterviewAgent] Generated {len(data['questions'])} opening questions via OpenAI")
            return data["questions"]

        logger.warning("[InterviewAgent] OpenAI failed for opening questions — using curated fallback pool")
        fallback = [
            {
                "id": 1,
                "text": "Hey there! Welcome to the interview. I'm your AI interviewer today — go ahead and introduce yourself! Tell me a bit about who you are and what you've been working on lately.",
                "category": "behavioral",
                "difficulty": "easy",
                "evaluating": "Self-introduction and communication",
            }
        ]
        categories = ["experience_validation", "technical", "problem_solving", "domain"]
        for i, cat in enumerate(categories[:num_questions - 1]):
            pool = _FALLBACK_QUESTION_POOLS.get(cat, _FALLBACK_QUESTION_POOLS["technical"])
            q = pool[0].copy()
            q["id"] = i + 2
            fallback.append(q)
        return fallback

    async def generate_follow_up(
        self,
        job_description: str,
        resume_text: str,
        transcript_so_far: List[Dict[str, str]],
        current_answer: str,
        current_question: Dict[str, Any],
        questions_asked: Optional[List[str]] = None,
        in_person_transcript: str = "",
        emotion_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Generate a follow-up question based on the candidate's answer."""
        quality = _answer_quality(current_answer)
        asked_texts = questions_asked or [
            e["text"] for e in transcript_so_far
            if e.get("type") == "question" or e.get("speaker") == "AI Interviewer"
        ]

        transcript_text = "\n".join(
            [f"[{m.get('timestamp', '')}] {m['speaker']}: {m['text']}" for m in transcript_so_far[-20:]]
        )

        # Count poor answers in a row
        recent_answers = [e for e in transcript_so_far if e.get("speaker") == "Candidate"][-5:]
        poor_streak = 0
        for a in reversed(recent_answers):
            q = _answer_quality(a.get("text", ""))
            if q in ("gibberish", "very_short"):
                poor_streak += 1
            else:
                break

        uncooperative_instruction = ""
        if poor_streak >= 3:
            uncooperative_instruction = f"""
WARNING: The candidate has given {poor_streak} consecutive non-substantive answers. They appear uncooperative.
- Stay friendly but try a COMPLETELY DIFFERENT, very easy topic
- Ask concrete factual questions (e.g., "What programming language did you use most recently?")
- Keep the tone warm, not frustrated
"""

        quality_instruction = {
            "gibberish": "The candidate's answer didn't make sense. Gently acknowledge it and ask a very simple, specific question on a new topic. Stay warm and encouraging.",
            "very_short": "Very brief answer. React briefly, then ask a more specific or easier question from a different angle.",
            "short": "Short but somewhat on-topic. Briefly react, then ask a targeted follow-up or shift to a new topic.",
            "adequate": "Decent answer. React positively and genuinely, then probe deeper or explore a new area.",
            "detailed": "Great, thorough answer! React enthusiastically, then challenge with something harder or explore a new area.",
        }

        # Build emotion context if available
        emotion_context = ""
        if emotion_data and isinstance(emotion_data, dict):
            dom = emotion_data.get("dominant", "unknown")
            eng = emotion_data.get("engagement", 0)
            stress = emotion_data.get("stress", 0)
            pos = emotion_data.get("positivity", 0)
            scores = emotion_data.get("scores", {})
            emotion_context = f"""
## Candidate's Facial Expression Analysis (during this answer)
Dominant Emotion: {dom}
Engagement Level: {eng}% | Stress Level: {stress}% | Positivity: {pos}%
Detailed: neutral={scores.get('neutral', 0):.0%}, happy={scores.get('happy', 0):.0%}, sad={scores.get('sad', 0):.0%}, angry={scores.get('angry', 0):.0%}, fearful={scores.get('fearful', 0):.0%}, surprised={scores.get('surprised', 0):.0%}

USE THIS INFORMATION TO:
- If candidate appears stressed/fearful: ask an easier, more encouraging question
- If candidate appears disengaged/neutral with low engagement: ask a more stimulating question
- If candidate appears happy/positive: continue probing deeper
- Factor the emotional state into your assessment — a nervous but correct answer is still a good answer
- Do NOT directly mention their detected emotions to the candidate
"""

        # Build in-person transcript context for follow-ups
        in_person_context = ""
        if in_person_transcript and in_person_transcript.strip():
            in_person_context = f"""
## In-Person Interview Transcript (from a previous round)
{in_person_transcript[:2000]}

IMPORTANT: Cross-reference the candidate's current answers with the in-person transcript.
- Note any inconsistencies between what they said before and now
- Build on topics they mentioned in person but didn't elaborate
- Do NOT re-ask the same questions from the in-person interview
"""

        prompt = f"""You are conducting a LIVE voice interview as a friendly, human-like interviewer. Generate the next conversational response + question based on the candidate's latest answer.

IMPORTANT — This is a VOICE conversation. Your response should:
1. First BRIEFLY acknowledge/react to what the candidate just said (1-2 sentences max)
2. Then naturally transition to your next question
3. Sound like a real person talking — use contractions, casual language
4. NEVER sound like a robot reading from a script

Examples of good conversational flow:
- "Oh nice, that's really interesting! So you mentioned working with React — what was the trickiest part of that project?"
- "Got it, that makes sense. I'm curious though — when you ran into that performance issue, how did you go about debugging it?"
- "Hmm, okay. Let me switch gears a bit — can you tell me about a time you had to work under a really tight deadline?"

## Job Description
{job_description}

## Resume
{resume_text}

## Interview Transcript So Far
{transcript_text}

## Current Question Asked
{current_question.get('text', '')}

## Candidate's Latest Answer
"{current_answer}"

## Answer Quality Assessment
Quality: {quality}
{quality_instruction.get(quality, '')}
{uncooperative_instruction}

## Previously Asked Questions (DO NOT repeat any)
{chr(10).join(f'- {q}' for q in asked_texts[-15:])}
{emotion_context}
{in_person_context}
RULES (CRITICAL):
1. The "reply" field is your BRIEF, natural reaction to their answer (1-2 sentences MAX). Example: "That's a great point about scalability!" or "Interesting, I hadn't thought about it that way."
2. The "question.text" field is ONLY the next question — do NOT include any reaction in it. Example: "What was the biggest technical challenge you faced in that project?"
3. NEVER say "Can you elaborate more on that?" or any variant
4. NEVER repeat a previously asked question
5. Sound HUMAN — use contractions, be warm, react genuinely
6. Keep the reply under 2 sentences and the question under 2 sentences (this is spoken aloud)
7. Choose the right agent/category based on what makes sense to ask next:
   - If you want to probe technical skills/projects → "technical"
   - If you want to explore teamwork/challenges/personal growth → "behavioral"  
   - If you want to test domain/industry knowledge → "domain"
   - If you want them to solve or describe solving a problem → "problem_solving"
   - If you want to verify experience claims → "experience_validation"
8. Assess the answer honestly — gibberish/no-answer gets score below 20

Respond in JSON:
{{
    "reply": {{
        "text": "Your brief natural reaction to their answer (1-2 sentences)",
        "category": "same category as the question they just answered"
    }},
    "question": {{
        "text": "Your next question ONLY (no reaction/preamble)",
        "category": "technical/behavioral/domain/problem_solving/experience_validation",
        "difficulty": "easy/medium/hard",
        "evaluating": "What this tests",
        "key_points": ["expected point 1"]
    }},
    "answer_assessment": {{
        "quality": "excellent/good/average/poor/no_answer",
        "score": 0-100,
        "key_points_hit": ["point1"],
        "missed_points": ["point2"],
        "note": "Honest assessment of this specific answer",
        "emotional_alignment": "How well the candidate's emotional state aligned with their verbal response (e.g., confident delivery, nervous but accurate, disengaged)"
    }}
}}"""

        data = await self._call_openai(
            system_prompt=(
                "You are a friendly, warm human interviewer having a real VOICE conversation. "
                "You MUST return a separate 'reply' (your reaction to their answer) and 'question' (your next question). "
                "The reply should be from the SAME agent category that asked the question they just answered. "
                "The question should be from whatever agent category makes sense for the next topic. "
                "Sound casual and human — use contractions, brief reactions like 'Oh nice!', 'Interesting!', 'Got it!'. "
                "NEVER say 'Can you elaborate more on that?' — always ask specific, targeted questions. "
                "Keep both reply and question SHORT since they are spoken aloud. "
                "If the candidate gives poor answers, gently redirect with an easier question."
            ),
            user_prompt=prompt,
            max_tokens=1024,
            temperature=0.6,
        )

        if data:
            # Extract reply and question
            reply = data.get("reply", {})
            if not reply or not isinstance(reply, dict) or not reply.get("text"):
                # If the model didn't return a separate reply, try to extract from old combined format
                q_text = data.get("question", {}).get("text", "")
                reply = {"text": "Got it.", "category": current_question.get("category", "general")}

            # Validate no "elaborate" question
            q_text = data.get("question", {}).get("text", "")
            if "elaborate" in q_text.lower() or "tell me more" in q_text.lower():
                logger.warning("[InterviewAgent] OpenAI returned 'elaborate' question, replacing")
                next_cat = "technical" if quality in ("gibberish", "very_short") else "behavioral"
                data["question"] = self._get_fallback_question(next_cat, asked_texts)

            # Ensure reply has a category
            if not reply.get("category"):
                reply["category"] = current_question.get("category", "general")
            data["reply"] = reply

            # Enforce honest scoring for poor answers
            assessment = data.get("answer_assessment", {})
            if quality in ("gibberish", "very_short") and assessment.get("score", 50) > 30:
                assessment["score"] = max(5, min(20, assessment.get("score", 10)))
                assessment["quality"] = "poor" if quality == "very_short" else "no_answer"
                assessment["note"] = f"Candidate response was {quality}: '{current_answer[:50]}'"
                data["answer_assessment"] = assessment

            logger.info(f"[InterviewAgent] Follow-up: quality={quality}, score={assessment.get('score', '?')}")
            return data

        # Fallback — OpenAI completely failed
        logger.warning("[InterviewAgent] OpenAI failed for follow-up — using intelligent fallback")

        current_cat = current_question.get("category", "technical")
        next_categories = ["behavioral", "problem_solving", "experience_validation", "domain", "technical"]
        next_cat = next((c for c in next_categories if c != current_cat), "behavioral")
        if quality in ("gibberish", "very_short") or poor_streak >= 2:
            next_cat = "experience_validation"

        fallback_q = self._get_fallback_question(next_cat, asked_texts)

        # Build a fallback reply
        fallback_replies = {
            "gibberish": "I didn't quite catch that, no worries.",
            "very_short": "Okay, let me try a different angle.",
            "short": "Alright, thanks for that.",
            "adequate": "Got it, thanks for sharing.",
            "detailed": "That was really insightful, thanks!",
        }
        fallback_reply = {
            "text": fallback_replies.get(quality, "Got it."),
            "category": current_cat,
        }

        if quality == "gibberish":
            score, quality_label = 5, "no_answer"
        elif quality == "very_short":
            score, quality_label = 15, "poor"
        elif quality == "short":
            score, quality_label = 35, "average"
        else:
            score, quality_label = 55, "good"

        return {
            "reply": fallback_reply,
            "question": fallback_q,
            "answer_assessment": {
                "quality": quality_label,
                "score": score,
                "key_points_hit": [],
                "missed_points": ["No substantive content provided"] if quality in ("gibberish", "very_short") else [],
                "note": f"Answer quality: {quality}. Response: '{current_answer[:80]}'"
            },
        }

    async def evaluate_full_interview(
        self, job_description: str, resume_text: str, transcript: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Evaluate the complete interview transcript for scoring."""
        transcript_text = "\n".join(
            [f"[{m.get('timestamp', '')}] {m['speaker']}: {m['text']}" for m in transcript]
        )

        candidate_answers = [m["text"] for m in transcript if m.get("speaker") == "Candidate"]
        total_answers = len(candidate_answers)
        gibberish_count = sum(1 for a in candidate_answers if _is_gibberish(a))
        short_count = sum(1 for a in candidate_answers if _answer_quality(a) in ("very_short", "short"))

        quality_context = ""
        if total_answers > 0:
            gibberish_pct = gibberish_count / total_answers * 100
            if gibberish_pct > 50:
                quality_context = f"""
CRITICAL: {gibberish_count} out of {total_answers} answers ({gibberish_pct:.0f}%) were gibberish or non-answers.
This candidate was LARGELY UNCOOPERATIVE. Scores MUST be very low (5-20 range).
Do NOT give average scores to someone who didn't answer."""
            elif (gibberish_count + short_count) / total_answers > 0.6:
                quality_context = f"""
WARNING: {gibberish_count + short_count} out of {total_answers} answers were very short or non-substantive.
This candidate struggled significantly. Most scores should be below 30."""

        prompt = f"""You are a senior hiring evaluator. Analyze this complete interview transcript.

## Job Description
{job_description}

## Resume
{resume_text}

## Full Interview Transcript
{transcript_text}

{quality_context}

SCORING RULES:
- Every score MUST be backed by specific transcript evidence
- Gibberish/no-answers = scores 5-25
- Short/vague answers = scores below 40
- A score of 50 means "meets basic expectations with evidence" — NOT a default
- Differentiate between areas

Respond in JSON:
{{
    "technical_score": 0-100,
    "behavior_score": 0-100,
    "domain_score": 0-100,
    "communication_score": 0-100,
    "problem_solving_score": 0-100,
    "learning_potential": 0-100,
    "risk_score": 0-100,
    "confidence": 0-100,
    "final_decision": "Strong Hire/Hire/Hold/Reject",
    "decision_reasoning": "Detailed reasoning citing SPECIFIC answers.",
    "strengths": [{{"area": "...", "evidence": "...", "transcript_ref": "Q#"}}],
    "weaknesses": [{{"area": "...", "evidence": "...", "transcript_ref": "Q#"}}],
    "question_analysis": [
        {{
            "question_number": 1,
            "question_text": "...",
            "answer_quality": "excellent/good/average/poor/no_answer",
            "score": 0-100,
            "key_insights": "What this revealed about the candidate"
        }}
    ],
    "overall_summary": "Comprehensive honest summary.",
    "hiring_recommendation": {{
        "decision": "Strong Hire/Hire/Hold/Reject",
        "confidence_level": 0-100,
        "key_factors": ["factor1"],
        "risk_factors": ["risk1"],
        "suggested_level": "Junior/Mid/Senior/Staff/Not Qualified"
    }}
}}"""

        data = await self._call_openai(
            system_prompt="You are a thorough, HONEST hiring evaluator. Do not sugarcoat poor performance. Every score must be backed by evidence.",
            user_prompt=prompt,
            max_tokens=8192,
            temperature=0.3,
        )

        if data:
            logger.info(f"[InterviewAgent] Evaluation: decision={data.get('final_decision')}, tech={data.get('technical_score')}")
            return data

        logger.warning("[InterviewAgent] OpenAI failed for evaluation — generating honest fallback")
        if total_answers > 0 and gibberish_count / total_answers > 0.5:
            return {
                "technical_score": 10, "behavior_score": 15, "domain_score": 10,
                "communication_score": 10, "problem_solving_score": 10, "learning_potential": 15,
                "risk_score": 85, "confidence": 70, "final_decision": "Reject",
                "decision_reasoning": f"Candidate provided {gibberish_count} non-substantive answers out of {total_answers} questions.",
                "strengths": [], "weaknesses": [{"area": "All Areas", "evidence": "No substantive answers", "transcript_ref": "All"}],
                "question_analysis": [], "overall_summary": "Candidate was largely unresponsive.",
                "hiring_recommendation": {"decision": "Reject", "confidence_level": 70, "key_factors": ["No demonstrated competence"], "risk_factors": ["Non-engagement"], "suggested_level": "Not Qualified"},
            }
        return {
            "technical_score": 30, "behavior_score": 30, "domain_score": 30,
            "communication_score": 30, "problem_solving_score": 30, "learning_potential": 30,
            "risk_score": 60, "confidence": 40, "final_decision": "Hold",
            "decision_reasoning": "Evaluation could not be fully completed due to a system error. Scores are conservative estimates.",
        }

    async def extract_resume_data(self, resume_text: str) -> Dict[str, Any]:
        """Extract structured data from resume text."""
        prompt = f"""Extract structured information from this resume.

## Resume Text
{resume_text}

Respond in JSON with ALL fields filled:
{{
    "name": "Full Name",
    "email": "email@example.com",
    "phone": "phone number or null",
    "location": "City, Country or null",
    "summary": "Brief professional summary",
    "experience_years": 5,
    "skills": {{
        "technical": ["Python", "React", "AWS"],
        "soft": ["Leadership", "Communication"],
        "tools": ["Docker", "Git"]
    }},
    "experience": [
        {{
            "company": "Company Name",
            "role": "Job Title",
            "duration": "Jan 2020 - Present",
            "highlights": ["Achieved X", "Built Y"]
        }}
    ],
    "education": [
        {{
            "institution": "University Name",
            "degree": "B.Tech in CS",
            "year": "2020"
        }}
    ],
    "projects": [
        {{
            "name": "Project X",
            "description": "Brief description",
            "technologies": ["React", "Node.js"]
        }}
    ],
    "certifications": ["AWS Solutions Architect", "etc"],
    "complexity_level": "junior/mid/senior/staff"
}}"""

        data = await self._call_openai(
            system_prompt="You are an expert resume parser. Extract all possible information accurately.",
            user_prompt=prompt,
            max_tokens=4096,
            temperature=0.2,
        )

        if data:
            return data
        return {"error": "extraction_failed", "name": "", "skills": {"technical": [], "soft": [], "tools": []}}


# Singleton
interview_agent = InterviewAgent()
