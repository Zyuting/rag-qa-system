"""LLM client abstraction for the RAG QA system.

Wraps the OpenAI-compatible Qwen API with retry logic.
Supports configuration via environment variables.
"""
import time
from typing import Optional

from openai import OpenAI

from backend.config import DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, QWEN_MODEL


_MAX_RETRIES = 3
_RETRY_DELAY_SEC = 1.0


def get_client() -> OpenAI:
    """Create an OpenAI-compatible client for Qwen API.

    Raises:
        RuntimeError: If DASHSCOPE_API_KEY is not configured.
    """
    if not DASHSCOPE_API_KEY:
        raise RuntimeError("DASHSCOPE_API_KEY not configured in .env")
    return OpenAI(api_key=DASHSCOPE_API_KEY, base_url=DASHSCOPE_BASE_URL)


def call_llm(prompt: str, temperature: float = 0.3, max_tokens: int = 1024) -> str:
    """Send a prompt to the LLM with exponential backoff retry.

    Args:
        prompt: The formatted prompt string.
        temperature: Generation temperature (default 0.3).
        max_tokens: Maximum token count in response (default 1024).

    Returns:
        The LLM's response text.

    Raises:
        RuntimeError: If all retries are exhausted.
    """
    client = get_client()
    last_error: Optional[Exception] = None

    for attempt in range(_MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=QWEN_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            last_error = e
            if attempt < _MAX_RETRIES - 1:
                delay = _RETRY_DELAY_SEC * (2 ** attempt)
                print(f"[WARN] LLM call failed (attempt {attempt + 1}/{_MAX_RETRIES}): {e}. Retrying in {delay:.1f}s...")
                time.sleep(delay)

    raise RuntimeError(f"LLM call failed after {_MAX_RETRIES} retries: {last_error}")
