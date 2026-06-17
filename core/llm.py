"""
Local LLM client backed by Ollama.

Replaces the previous AWS Bedrock (Claude Haiku) text-generation calls.
- generate(): non-streaming, with optional forced-JSON (Ollama `format` + validate/retry)
- generate_stream(): async token generator

The model defaults to settings.OLLAMA_MODEL (llama3.1:8b); pass settings.OLLAMA_FAST_MODEL
(llama3.2:3b) for lightweight helper calls (title, intent/query analysis).
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

    - If `json_schema` is provided, Ollama is constrained to it via `format`, the reply is
      parsed as JSON, validated to contain the schema's required keys, and retried once on
      failure. Returns a dict.
    - Otherwise returns the raw assistant text (str).
    """
    payload: dict = {
        "model": model or settings.OLLAMA_MODEL,
        "messages": _build_messages(prompt, system),
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    if json_schema is not None:
        payload["format"] = json_schema

    url = f"{settings.OLLAMA_BASE_URL}/api/chat"

    async def _call() -> str:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()["message"]["content"]

    if json_schema is None:
        return await _call()

    required = json_schema.get("required", [])
    last_err: Optional[Exception] = None
    for _ in range(2):  # initial attempt + one retry
        try:
            parsed = json.loads(await _call())
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
    model: Optional[str] = None,
) -> AsyncIterator[str]:
    """Stream assistant text deltas from Ollama's /api/chat (stream=true)."""
    payload = {
        "model": model or settings.OLLAMA_MODEL,
        "messages": _build_messages(prompt, system),
        "stream": True,
        "options": {"temperature": temperature, "num_predict": max_tokens},
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
