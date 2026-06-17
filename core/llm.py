"""
Local LLM client backed by Ollama (default model: llama3.2:3b).

Replaces the previous AWS Bedrock (Claude Haiku) text-generation calls.
Exposes a non-streaming `generate` (with optional structured JSON output) and
a `generate_stream` async generator.
"""
import json
from typing import Any, AsyncIterator, Optional

import httpx

from core.config import settings


class OllamaError(RuntimeError):
    pass


def _build_messages(prompt: str, system: Optional[str]) -> list[dict]:
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


async def generate(
    prompt: str,
    system: Optional[str] = None,
    max_tokens: int = 512,
    temperature: float = 0.0,
    json_schema: Optional[dict] = None,
    timeout: float = 300.0,
    model: Optional[str] = None,
) -> Any:
    """
    Call Ollama's /api/chat (non-streaming).

    - `model` defaults to settings.OLLAMA_MODEL; pass settings.OLLAMA_FAST_MODEL for
      lightweight helper calls (title/analysis) that don't need the main model.
    - If `json_schema` is provided, Ollama is asked to constrain output to that
      schema (via the `format` parameter), the reply is parsed as JSON, validated
      to contain the schema's required keys, and retried once on failure. Returns a dict.
    - Otherwise returns the raw assistant text (str).
    """
    payload: dict = {
        "model": model or settings.OLLAMA_MODEL,
        "messages": _build_messages(prompt, system),
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    if json_schema is not None:
        payload["format"] = json_schema

    url = f"{settings.OLLAMA_BASE_URL}/api/chat"

    async def _call() -> str:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data["message"]["content"]

    if json_schema is None:
        return await _call()

    required = json_schema.get("required", [])
    last_err: Optional[Exception] = None
    for _ in range(2):  # initial attempt + one retry
        try:
            content = await _call()
            parsed = json.loads(content)
            if all(key in parsed for key in required):
                return parsed
            last_err = OllamaError(f"Missing required keys {required} in: {parsed}")
        except (json.JSONDecodeError, KeyError) as e:
            last_err = e
    raise OllamaError(f"Failed to get valid structured output from Ollama: {last_err}")


async def generate_stream(
    prompt: str,
    system: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 0.4,
    timeout: float = 300.0,
) -> AsyncIterator[str]:
    """Stream assistant text deltas from Ollama's /api/chat (stream=true)."""
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": _build_messages(prompt, system),
        "stream": True,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    url = f"{settings.OLLAMA_BASE_URL}/api/chat"

    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", url, json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                chunk = json.loads(line)
                token = chunk.get("message", {}).get("content", "")
                if token:
                    yield token
                if chunk.get("done"):
                    break
