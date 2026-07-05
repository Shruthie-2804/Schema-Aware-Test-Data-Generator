"""
ai_provider.py
--------------
Provider-based AI abstraction layer for the AI-Powered Schema-Aware Test Data Generator.

Supports:
  - Google Gemini (free tier via REST API)
  - OpenAI-compatible endpoints (OpenAI, Groq, etc.)
  - Fallback (no AI — pure Faker mode)

Design:
  - BaseAIProvider defines the contract.
  - Each concrete provider implements `complete(prompt) -> str`.
  - `get_provider()` reads AI_PROVIDER from .env and returns the right instance.
  - If the key is missing or the provider is unavailable, FallbackProvider is used
    and callers receive a clear explanation in the response.

Never hardcode API keys. All secrets are loaded from environment variables.
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base interface
# ---------------------------------------------------------------------------

class BaseAIProvider(ABC):
    """Abstract base class every AI provider must implement."""

    @abstractmethod
    def complete(self, prompt: str, max_tokens: int = 4096) -> str:
        """Send a prompt and return the text completion."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the provider is properly configured."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name."""
        ...


# ---------------------------------------------------------------------------
# Fallback provider — used when AI is not configured
# ---------------------------------------------------------------------------

class FallbackProvider(BaseAIProvider):
    """
    Used when no AI provider is configured or the key is missing.
    Returns a structured error message so the system can degrade gracefully
    to pure Faker-only generation.
    """

    @property
    def provider_name(self) -> str:
        return "fallback"

    def is_available(self) -> bool:
        return False

    def complete(self, prompt: str, max_tokens: int = 4096) -> str:
        return (
            "AI_UNAVAILABLE: No AI provider is configured. "
            "Set AI_PROVIDER and the corresponding API key in your .env file. "
            "The system will use Faker-only generation as a fallback."
        )


# ---------------------------------------------------------------------------
# Gemini provider (Google Generative Language REST API)
# ---------------------------------------------------------------------------

class GeminiProvider(BaseAIProvider):
    """
    Google Gemini provider using the free-tier REST API.
    Requires GEMINI_API_KEY in .env.
    Uses gemini-1.5-flash by default (free quota-friendly).
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    DEFAULT_MODEL = "gemini-1.5-flash"

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model = os.getenv("GEMINI_MODEL", self.DEFAULT_MODEL)

    @property
    def provider_name(self) -> str:
        return f"gemini/{self.model}"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key != "your_api_key_here")

    def complete(self, prompt: str, max_tokens: int = 4096) -> str:
        if not self.is_available():
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Please add it to your .env file."
            )

        import urllib.request
        import urllib.error

        url = f"{self.BASE_URL}/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.7,
            },
        }
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Gemini API error {e.code}: {error_body}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error contacting Gemini: {e.reason}") from e
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected Gemini response structure: {e}") from e




# ---------------------------------------------------------------------------
# OpenAI-compatible provider (OpenAI, Groq, Together, etc.)
# ---------------------------------------------------------------------------

class OpenAICompatibleProvider(BaseAIProvider):
    """
    OpenAI-compatible chat completion provider.
    Works with OpenAI, Groq (free tier), Together AI, etc.

    Required .env:
      OPENAI_API_KEY   — API key
      OPENAI_BASE_URL  — optional, defaults to https://api.openai.com/v1
      OPENAI_MODEL     — optional, defaults to gpt-4o-mini
    """

    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.base_url = os.getenv("OPENAI_BASE_URL", self.DEFAULT_BASE_URL).rstrip("/")
        self.model = os.getenv("OPENAI_MODEL", self.DEFAULT_MODEL)

    @property
    def provider_name(self) -> str:
        return f"openai-compat/{self.model}"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key != "your_api_key_here")

    def complete(self, prompt: str, max_tokens: int = 4096) -> str:
        if not self.is_available():
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Please add it to your .env file."
            )

        import urllib.request
        import urllib.error

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI API error {e.code}: {error_body}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error contacting OpenAI: {e.reason}") from e
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected API response structure: {e}") from e


# ---------------------------------------------------------------------------
# Factory — get the configured provider
# ---------------------------------------------------------------------------

def get_provider() -> BaseAIProvider:
    """
    Read AI_PROVIDER from environment and return the appropriate provider.
    Falls back to FallbackProvider if AI is not configured.

    Supported values for AI_PROVIDER:
      gemini   → GeminiProvider
      openai   → OpenAICompatibleProvider (also works for Groq with OPENAI_BASE_URL)
      none     → FallbackProvider (explicit opt-out)
    """
    provider_name = os.getenv("AI_PROVIDER", "fallback").lower().strip()

    if provider_name == "gemini":
        p = GeminiProvider()
        if not p.is_available():
            logger.warning(
                "AI_PROVIDER=gemini but GEMINI_API_KEY is missing or placeholder. "
                "Falling back to Faker-only mode."
            )
            return FallbackProvider()
        return p

    elif provider_name in ("openai", "groq"):
        p = OpenAICompatibleProvider()
        if not p.is_available():
            logger.warning(
                "AI_PROVIDER=%s but OPENAI_API_KEY is missing. "
                "Falling back to Faker-only mode.", provider_name
            )
            return FallbackProvider()
        return p

    else:
        # "fallback", "none", or anything unrecognised
        if provider_name not in ("fallback", "none", ""):
            logger.warning("Unknown AI_PROVIDER=%r. Using fallback mode.", provider_name)
        return FallbackProvider()
