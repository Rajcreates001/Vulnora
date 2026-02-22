"""LLM client wrapper supporting OpenAI, Anthropic, and Groq with retry logic."""

import asyncio
import re
import time
import logging
from typing import Any, Dict, List, Optional

from config import settings

logger = logging.getLogger(__name__)

# Singleton clients — reuse across calls
_openai_client = None
_anthropic_client = None
_groq_client = None
_ollama_client = None

MAX_RETRIES = 2
RETRY_DELAYS = [1, 3]

# Time-based provider disable: provider -> expiry timestamp
# Providers are disabled for 60 seconds, then re-enabled automatically
_disabled_until: Dict[str, float] = {}
DISABLE_DURATION = 60  # seconds

# Quota / auth errors → disable the provider temporarily
QUOTA_ERROR_KEYWORDS = [
    "insufficient_quota",
    "exceeded your current quota",
    "credit balance",
    "billing",
    "account_deactivated",
]

AUTH_ERROR_KEYWORDS = [
    "authentication",
    "invalid_api_key",
    "permission",
    "invalid x-api-key",
    "not found",
    "connection refused",
    "offline"
]


def _is_quota_error(error: Exception) -> bool:
    """Billing / quota errors — disable provider for a while, no retries."""
    err_str = str(error).lower()
    for kw in QUOTA_ERROR_KEYWORDS:
        if kw in err_str:
            return True
    return False


def _is_auth_error(error: Exception) -> bool:
    """Auth errors — disable provider, no retries."""
    err_str = str(error).lower()
    for kw in AUTH_ERROR_KEYWORDS:
        if kw in err_str:
            return True
    status_code = getattr(error, "status_code", None) or getattr(error, "status", None)
    if status_code in (401, 403):
        return True
    return False


def _is_rate_limit(error: Exception) -> bool:
    """True 429 rate limit (NOT quota) — retry with backoff."""
    # Quota errors look like rate limits (OpenAI returns 429) but are NOT
    if _is_quota_error(error):
        return False
    status_code = getattr(error, "status_code", None) or getattr(error, "status", None)
    if status_code == 429:
        return True
    err_str = str(error).lower()
    if "rate_limit" in err_str or "rate limit" in err_str or "too many requests" in err_str:
        return True
    return False


def _should_skip_provider(provider: str) -> bool:
    """Check if a provider is temporarily disabled."""
    if provider in _disabled_until:
        if time.time() < _disabled_until[provider]:
            return True
        # Expired — re-enable
        del _disabled_until[provider]
    return False


def _disable_provider(provider: str):
    """Temporarily disable a provider."""
    _disabled_until[provider] = time.time() + DISABLE_DURATION
    logger.warning(f"Provider '{provider}' disabled for {DISABLE_DURATION}s")


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


def _get_groq_client():
    global _groq_client
    if _groq_client is None:
        from openai import AsyncOpenAI
        _groq_client = AsyncOpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )
    return _groq_client


def _get_ollama_client():
    global _ollama_client
    if _ollama_client is None:
        from openai import AsyncOpenAI
        _ollama_client = AsyncOpenAI(
            api_key="ollama",
            base_url=f"{settings.ollama_base_url.rstrip('/')}/v1",
        )
    return _ollama_client


def _get_provider_order() -> list:
    """Ordered list of providers. Evaluates primary first."""
    primary = settings.llm_provider
    provider_keys = {
        "ollama": "local",  # always assume available if specified
        "groq": settings.groq_api_key,
        "anthropic": settings.anthropic_api_key,
        "openai": settings.openai_api_key,
    }

    ordered = [primary] if primary in provider_keys else []
    for p in provider_keys:
        if p != primary:
            ordered.append(p)

    available = []
    for p in ordered:
        if not provider_keys.get(p):
            continue
        if _should_skip_provider(p):
            logger.debug(f"Skipping disabled provider '{p}'")
            continue
        available.append(p)
    return available


async def get_llm_response(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 4096,
    json_mode: bool = False,
) -> str:
    """Get a response from the configured LLM provider with retry + fallback."""
    providers = _get_provider_order()

    if not providers:
        raise Exception(
            "No LLM providers available. All providers are either disabled "
            "(quota/auth errors) or have no API key configured. "
            "Please add a valid API key to backend/.env "
            "(GROQ_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY)."
        )

    last_error = None

    for provider in providers:
        for attempt in range(MAX_RETRIES):
            try:
                result = await _call_provider(
                    provider, system_prompt, user_prompt,
                    temperature, max_tokens, json_mode,
                )
                return result

            except Exception as e:
                last_error = e
                err_str = str(e)[:200]
                logger.warning(f"LLM {provider} attempt {attempt+1}/{MAX_RETRIES}: {err_str}")

                # Quota exhaustion — disable provider, skip all retries
                if _is_quota_error(e):
                    _disable_provider(provider)
                    break

                # Auth error — disable provider, skip all retries
                if _is_auth_error(e):
                    _disable_provider(provider)
                    break

                # Rate limit — retry with long backoff
                if _is_rate_limit(e):
                    if attempt < MAX_RETRIES - 1:
                        delay = max(RETRY_DELAYS[attempt], 10)
                        logger.info(f"Rate limited on {provider}, waiting {delay}s...")
                        await asyncio.sleep(delay)
                    continue

                # Other errors (context too long, bad request, etc.)
                # Retry with normal backoff, but don't disable provider
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAYS[attempt])

    raise last_error or Exception("All LLM providers failed")


async def _call_provider(
    provider: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    json_mode: bool,
) -> str:
    if provider == "groq":
        result = await _call_groq(system_prompt, user_prompt, temperature, max_tokens, json_mode)
    elif provider == "ollama":
        result = await _call_ollama(system_prompt, user_prompt, temperature, max_tokens, json_mode)
    elif provider == "anthropic":
        result = await _call_anthropic(system_prompt, user_prompt, temperature, max_tokens)
        if json_mode:
            result = _extract_json(result)
    else:
        result = await _call_openai(system_prompt, user_prompt, temperature, max_tokens, json_mode)
    return result


def _extract_json(text: str) -> str:
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


async def _call_openai(
    system_prompt: str, user_prompt: str,
    temperature: float, max_tokens: int, json_mode: bool,
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
    system_prompt: str, user_prompt: str,
    temperature: float, max_tokens: int,
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


async def _call_groq(
    system_prompt: str, user_prompt: str,
    temperature: float, max_tokens: int, json_mode: bool,
) -> str:
    client = _get_groq_client()
    max_tokens = min(max_tokens, 8192)

    # Truncate prompts if too long for Groq's context window
    # llama-3.3-70b-versatile has ~128K context but Groq free tier may limit it
    max_prompt_chars = 90000  # ~22K tokens, safe for free tier
    if len(system_prompt) + len(user_prompt) > max_prompt_chars:
        # Trim user_prompt to fit, keeping system_prompt intact
        available = max_prompt_chars - len(system_prompt)
        user_prompt = user_prompt[:available] + "\n\n[... content truncated for context limit ...]"

    kwargs: Dict[str, Any] = {
        "model": "llama-3.3-70b-versatile",
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


async def _call_ollama(
    system_prompt: str, user_prompt: str,
    temperature: float, max_tokens: int, json_mode: bool,
) -> str:
    client = _get_ollama_client()
    max_tokens = min(max_tokens, 8192)

    kwargs: Dict[str, Any] = {
        "model": settings.ollama_model,
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


async def get_embedding(text: str) -> List[float]:
    """Get text embedding. Falls back to hash-based embedding if no provider works."""
    if settings.openai_api_key and not _should_skip_provider("openai"):
        try:
            client = _get_openai_client()
            response = await client.embeddings.create(model="text-embedding-3-small", input=text)
            return response.data[0].embedding
        except Exception as e:
            if _is_quota_error(e) or _is_auth_error(e):
                _disable_provider("openai")
            logger.warning(f"Embedding fallback: {str(e)[:100]}")

    # Deterministic hash-based embedding fallback
    import hashlib
    h = hashlib.sha256(text.encode()).hexdigest()
    embedding = []
    for i in range(0, len(h), 2):
        val = int(h[i:i+2], 16) / 255.0
        embedding.append(val * 2 - 1)
    while len(embedding) < 1536:
        h = hashlib.sha256(h.encode()).hexdigest()
        for i in range(0, len(h), 2):
            if len(embedding) >= 1536:
                break
            val = int(h[i:i+2], 16) / 255.0
            embedding.append(val * 2 - 1)
    return embedding[:1536]
