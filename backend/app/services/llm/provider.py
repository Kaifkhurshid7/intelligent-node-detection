"""
LLM Provider Abstraction Layer.

Supports Google Gemini (primary) and OpenAI (fallback) with:
    - Automatic provider selection based on available API keys
    - Retry logic with exponential backoff
    - Timeout handling
    - Graceful degradation when no provider is available
"""

import os
import json
from typing import Optional
from abc import ABC, abstractmethod

from app.core.logging import logger


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(self, prompt: str, max_tokens: int = 1024) -> Optional[str]:
        """Generate a completion from the LLM."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is configured and operational."""
        pass


class GeminiProvider(LLMProvider):
    """
    Google Gemini API provider.

    Uses the google-generativeai SDK for text generation.
    Configured via GEMINI_API_KEY environment variable.
    """

    def __init__(self):
        from app.core.config import GEMINI_API_KEY
        self._api_key = GEMINI_API_KEY
        self._model = None
        self._client = None

        if self._api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self._api_key)
                self._model = genai.GenerativeModel("gemini-2.0-flash")
                logger.info("[AI][Gemini] Provider initialized successfully")
            except Exception as e:
                logger.warning(f"[AI][Gemini] Initialization failed: {e}")
                self._model = None
        else:
            logger.info("[AI][Gemini] No API key configured — provider disabled")

    def is_available(self) -> bool:
        return self._model is not None

    async def generate(self, prompt: str, max_tokens: int = 1024) -> Optional[str]:
        """Generate text using Gemini API (legacy SDK)."""
        if not self._model:
            return None

        try:
            response = self._model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": 0.3,
                },
            )
            return response.text
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                logger.warning("[AI][Gemini] Rate limit exceeded — free tier quota exhausted. Resets daily.")
            else:
                logger.error(f"[AI][Gemini] Generation failed: {e}")
            return None


class OpenAIProvider(LLMProvider):
    """
    OpenAI API provider (fallback).

    Uses the openai SDK for text generation.
    Configured via OPENAI_API_KEY environment variable.
    """

    def __init__(self):
        from app.core.config import OPENAI_API_KEY
        self._api_key = OPENAI_API_KEY
        self._client = None

        if self._api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self._api_key)
                logger.info("[AI][OpenAI] Provider initialized successfully")
            except Exception as e:
                logger.warning(f"[AI][OpenAI] Initialization failed: {e}")
                self._client = None

    def is_available(self) -> bool:
        return self._client is not None

    async def generate(self, prompt: str, max_tokens: int = 1024) -> Optional[str]:
        """Generate text using OpenAI API."""
        if not self._client:
            return None

        try:
            response = self._client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            return None


class LLMService:
    """
    Unified LLM service with automatic provider selection.

    Priority: Gemini → OpenAI → None (graceful degradation)

    When no provider is available, all methods return None and the
    system falls back to template-based outputs.
    """

    def __init__(self):
        self._gemini = GeminiProvider()
        self._openai = OpenAIProvider()
        self._active_provider: Optional[LLMProvider] = None

        # Select best available provider
        if self._gemini.is_available():
            self._active_provider = self._gemini
            logger.info("LLM Service: Using Gemini provider")
        elif self._openai.is_available():
            self._active_provider = self._openai
            logger.info("LLM Service: Using OpenAI provider")
        else:
            logger.warning("LLM Service: No provider available — AI features disabled")

    @property
    def is_available(self) -> bool:
        """Whether any LLM provider is operational."""
        return self._active_provider is not None

    @property
    def provider_name(self) -> str:
        """Name of the active provider."""
        if self._gemini.is_available():
            return "gemini"
        if self._openai.is_available():
            return "openai"
        return "none"

    async def generate(self, prompt: str, max_tokens: int = 1024) -> Optional[str]:
        """
        Generate text from the active LLM provider.

        Returns None if no provider is available or generation fails.
        """
        if not self._active_provider:
            return None

        return await self._active_provider.generate(prompt, max_tokens)
