"""LLM client wrapper supporting OpenAI and Anthropic with retry logic."""

import asyncio
import re
import logging
from typing import Any, Dict, List, Optional

from config import settings

logger = logging.getLogger(__name__)

# Singleton clients — reuse across calls
_openai_client = None
_anthropic_client = None

MAX_RETRIES = 3
RETRY_DELAYS = [2, 5, 10]  # seconds

# HTTP status codes that should NOT be retried (billing, auth, permission errors)
NON_RETRYABLE_KEYWORDS = [
    "credit balance",
    "insufficient_quota",
    "billing",
    "rate_limit",  # for 429 we catch separately
    "authentication",
    "invalid_api_key",
    "permission",
    "account_deactivated",
]


def _is_non_retryable(error: Exception) -> bool:
    """Check if an error is non-retryable (billing, auth, etc.)."""
    err_str = str(error).lower()
    # Check for known non-retryable error messages
    for keyword in NON_RETRYABLE_KEYWORDS:
        if keyword in err_str:
            return True
    # Check for HTTP status codes that indicate permanent failure
    status_code = getattr(error, "status_code", None) or getattr(error, "status", None)
    if status_code in (400, 401, 402, 403, 404):
        return True
    return False


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import AsyncOpenAI
        _openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _openai_client


def _get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None:
        from anthropic import AsyncAnthropic
        _anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client


async def get_llm_response(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 4096,
    json_mode: bool = False,
) -> str:
    """Get a response from the configured LLM provider with retry + fallback."""
    primary = settings.llm_provider
    fallback = "openai" if primary == "anthropic" else "anthropic"

    # Try primary provider with retries
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            if primary == "anthropic":
                result = await _call_anthropic(system_prompt, user_prompt, temperature, max_tokens)
            else:
                result = await _call_openai(system_prompt, user_prompt, temperature, max_tokens, json_mode)

            # For json_mode with anthropic, extract JSON from response
            if json_mode and primary == "anthropic":
                result = _extract_json(result)

            return result
        except Exception as e:
            last_error = e
            err_str = str(e)
            logger.warning(f"LLM attempt {attempt + 1}/{MAX_RETRIES} failed ({primary}): {err_str}")

            # If this is a non-retryable error (billing, auth), skip remaining retries
            if _is_non_retryable(e):
                logger.warning(f"Non-retryable error detected on {primary}, switching to fallback immediately")
                break

            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAYS[attempt])

    # Try fallback provider with its own retries
    logger.info(f"Primary provider {primary} failed. Switching to fallback: {fallback}")
    for attempt in range(MAX_RETRIES):
        try:
            if fallback == "anthropic":
                result = await _call_anthropic(system_prompt, user_prompt, temperature, max_tokens)
                if json_mode:
                    result = _extract_json(result)
            else:
                result = await _call_openai(system_prompt, user_prompt, temperature, max_tokens, json_mode)
            logger.info(f"Fallback provider {fallback} succeeded on attempt {attempt + 1}")
            return result
        except Exception as e2:
            logger.warning(f"Fallback attempt {attempt + 1}/{MAX_RETRIES} failed ({fallback}): {str(e2)}")

            # If fallback also has non-retryable error, fail fast
            if _is_non_retryable(e2):
                logger.error(f"Fallback provider {fallback} also has non-retryable error")
                break

            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAYS[attempt])

    # Both providers failed
    logger.error(f"All LLM providers failed. Primary: {primary}, Fallback: {fallback}")
    raise last_error or Exception("All LLM providers failed")


def _extract_json(text: str) -> str:
    """Extract JSON from text that may have markdown code blocks."""
    # Try to find JSON in code blocks
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Try to find raw JSON object/array
    match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


async def _call_openai(
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    json_mode: bool,
) -> str:
    client = _get_openai_client()
    kwargs: Dict[str, Any] = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = await client.chat.completions.create(**kwargs)
    return response.choices[0].message.content or ""


async def _call_anthropic(
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
) -> str:
    client = _get_anthropic_client()
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text if response.content else ""


async def get_embedding(text: str) -> List[float]:
    """Get text embedding using OpenAI."""
    client = _get_openai_client()
    response = await client.embeddings.create(model="text-embedding-3-small", input=text)
    return response.data[0].embedding
