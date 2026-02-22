"""Base agent class for all hiring panel agents."""

import json
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict
from openai import AsyncOpenAI
from config import get_settings

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds


class BaseAgent(ABC):
    """Abstract base class for all hiring panel agents."""

    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        self.model = self.settings.llm_model
        self.temperature = self.settings.llm_temperature

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def role(self) -> str:
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        pass

    async def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent on the given state and return updated state."""
        logger.info(f"[{self.name}] Starting analysis...")
        prompt = self.build_prompt(state)
        response = await self._call_llm(prompt)
        logger.info(f"[{self.name}] LLM response length: {len(response)} chars")
        result = self.parse_response(response, state)
        logger.info(f"[{self.name}] Analysis complete.")
        return result

    def build_prompt(self, state: Dict[str, Any]) -> str:
        """Build the user prompt from state. Override in subclasses."""
        resume = state.get("resume_text", "") or ""
        transcript = state.get("transcript_text", "") or ""
        job_desc = state.get("job_description", "") or ""

        return f"""
## Job Description
{job_desc}

## Candidate Resume
{resume}

## Interview Transcript
{transcript if transcript else "(No interview transcript available — evaluate based on resume and job description only. Score more conservatively when transcript evidence is missing.)"}

## Previous Agent Analyses
{self._format_previous_analyses(state)}

Provide your analysis as the {self.name}. Follow these MANDATORY rules:

1. EVIDENCE REQUIREMENT: Every score MUST be justified by citing SPECIFIC text from the resume or transcript. If you assign a score of 75, explain exactly what evidence supports 75 and not 60 or 90.

2. SCORING DISCIPLINE: 
   - All numeric scores must be integers between 1-100
   - NEVER give the same score for every metric — differentiate based on evidence
   - A score of 50 means "average/meets basic expectations" — not a default
   - Scores above 80 require STRONG evidence; scores below 40 indicate clear deficiency

3. REASONING DEPTH: Your summary must be 3-6 sentences minimum, referencing specific resume content or interview answers.

4. HONESTY: If evidence is insufficient to assess a metric, say so and score it around 40-50 (uncertain), NOT high.
"""

    async def _call_llm(self, user_prompt: str) -> str:
        """Call the LLM with retry logic for robustness."""
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"[{self.name}] LLM call attempt {attempt}/{MAX_RETRIES}")
                response = await self.client.chat.completions.create(
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.settings.llm_max_tokens,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content or "{}"
                logger.debug(f"[{self.name}] Raw LLM response: {content[:500]}")

                # Validate it's valid JSON before returning
                try:
                    parsed = json.loads(content)
                    if parsed.get("error"):
                        logger.warning(f"[{self.name}] LLM returned error in JSON: {parsed['error']}")
                        if attempt < MAX_RETRIES:
                            await asyncio.sleep(RETRY_DELAY * attempt)
                            continue
                    return content
                except json.JSONDecodeError:
                    logger.warning(f"[{self.name}] Invalid JSON from LLM (attempt {attempt}): {content[:200]}")
                    if attempt < MAX_RETRIES:
                        await asyncio.sleep(RETRY_DELAY * attempt)
                        continue
                    return content  # Return as-is, let parse_response handle it

            except Exception as e:
                last_error = e
                logger.error(f"[{self.name}] LLM call failed (attempt {attempt}): {e}")
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY * attempt)
                    continue

        logger.error(f"[{self.name}] All {MAX_RETRIES} LLM call attempts failed: {last_error}")
        return json.dumps({"error": f"Agent {self.name} failed after {MAX_RETRIES} retries: {str(last_error)}"})

    @abstractmethod
    def parse_response(self, response: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM response and update state."""
        pass

    def _safe_int(self, value: Any, default: int = 40) -> int:
        """Safely convert a value to int, returning default if invalid.
        Default changed from 50 to 40 to be more conservative."""
        if value is None:
            return default
        try:
            v = int(float(value))
            return max(0, min(100, v))
        except (ValueError, TypeError):
            return default

    def _format_previous_analyses(self, state: Dict[str, Any]) -> str:
        """Format previous agent analyses for context."""
        analyses = state.get("agent_analyses", {})
        if not analyses:
            return "No previous analyses available."

        parts = []
        for agent_name, analysis in analyses.items():
            parts.append(f"### {agent_name}\n{analysis}")
        return "\n\n".join(parts)

    # ─── Security Scan Agent Methods ────────────────────────
    # These methods are used by security scan agents (not hiring agents)
    
    async def log(
        self,
        project_id: str,
        message: str,
        log_type: str = "info",
        data: Any = None,
    ) -> None:
        """Log a message for security scan agents."""
        from db.supabase_client import store_agent_log
        try:
            await store_agent_log(project_id, self.name, message, log_type, data)
        except Exception as e:
            logger.error(f"Failed to store agent log: {e}")

    async def save_output(self, project_id: str, output: Any) -> None:
        """Save agent output for security scan agents."""
        from db.redis_client import store_agent_output
        try:
            await store_agent_output(project_id, self.name, output)
        except Exception as e:
            logger.error(f"Failed to store agent output: {e}")
            print(f"[SAVE OUTPUT ERROR] {project_id}/{self.name}: {e}")
