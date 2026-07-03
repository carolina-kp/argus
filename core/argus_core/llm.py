"""Provider-agnostic LLM interface (zero-cost mode).

Primary provider is chosen by `LLM_PROVIDER`; on failure the remaining
configured providers are tried in order. Prompts are provider-agnostic:
callers pass (system, user) and get text back.
"""
import logging
from typing import Any

import httpx

from argus_core.config import settings

logger = logging.getLogger("argus.llm")

_TIMEOUT = 60.0


class LLMError(RuntimeError):
    """Raised when every configured provider fails."""


async def _gemini(system: str, user: str) -> str:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent"
    )
    body: dict[str, Any] = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"temperature": 0.2},
    }
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(url, params={"key": settings.gemini_api_key}, json=body)
        resp.raise_for_status()
        data = resp.json()
    text: str = data["candidates"][0]["content"]["parts"][0]["text"]
    return text


async def _groq(system: str, user: str) -> str:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json={
                "model": settings.groq_model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.2,
            },
        )
        resp.raise_for_status()
        data = resp.json()
    text: str = data["choices"][0]["message"]["content"]
    return text


async def _anthropic(system: str, user: str) -> str:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": settings.anthropic_model,
                "max_tokens": 2048,
                "system": system,
                "messages": [{"role": "user", "content": user}],
                "temperature": 0.2,
            },
        )
        resp.raise_for_status()
        data = resp.json()
    text: str = data["content"][0]["text"]
    return text


def _provider_chain() -> list[str]:
    """Primary first, then any other provider that has a key configured."""
    keys = {
        "gemini": settings.gemini_api_key,
        "groq": settings.groq_api_key,
        "anthropic": settings.anthropic_api_key,
    }
    chain = [settings.llm_provider] if keys.get(settings.llm_provider) else []
    chain += [p for p, k in keys.items() if k and p not in chain]
    return chain


async def generate(system: str, user: str) -> str:
    """Generate text via the first working configured provider."""
    fns = {"gemini": _gemini, "groq": _groq, "anthropic": _anthropic}
    chain = _provider_chain()
    if not chain:
        raise LLMError("no LLM provider configured (set GEMINI_API_KEY or GROQ_API_KEY)")
    last: Exception | None = None
    for name in chain:
        try:
            return await fns[name](system, user)
        except Exception as exc:  # noqa: BLE001 - fall through to next provider
            logger.warning('{"llm":"%s","event":"provider_failed","error":"%s"}', name, exc)
            last = exc
    raise LLMError(f"all LLM providers failed: {last}") from last
