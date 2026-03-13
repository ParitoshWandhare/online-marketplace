# gift_ai_service/core/gemini_client.py
"""
Direct Gemini REST Client
=========================
Bypasses the google-generativeai library's v1beta routing entirely.
Calls the v1 REST endpoint directly using google-auth for authentication.

Why this exists:
- google-generativeai <= 0.8.3 routes ALL requests through v1beta
- v1beta no longer supports gemini-1.5-flash, gemini-1.5-pro, gemini-pro (404)
- gemini-2.0-flash works on v1beta but hits free-tier 429s quickly
- This client calls https://generativelanguage.googleapis.com/v1/models/{model}:generateContent
  directly, which supports all current models regardless of library version

Usage:
    from core.gemini_client import GeminiDirectClient
    client = GeminiDirectClient()
    text = await client.generate(prompt)
"""

import os
import json
import logging
import asyncio
import httpx
from typing import Optional, List

logger = logging.getLogger("gift_ai.gemini_client")

# v1 REST endpoint — never v1beta
GEMINI_V1_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Model preference order for text generation
# All of these are available on the v1 endpoint
TEXT_MODEL_CHAIN: List[str] = [
    "gemini-1.5-flash-8b",      # smallest, highest free-tier RPM (1000/min)
    "gemini-1.5-flash",         # good balance, 500 RPM free
    "gemini-1.5-pro",           # most capable 1.5, 50 RPM free
    "gemini-2.0-flash-lite",    # newest lite
    "gemini-2.0-flash",         # newest full
]

# Model preference order for vision (multimodal) generation
VISION_MODEL_CHAIN: List[str] = [
    "gemini-1.5-flash-8b",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
]


class GeminiDirectClient:
    """
    Calls Gemini v1 REST API directly.
    Handles 429 rate limits with exponential backoff and automatic model fallback.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY environment variable is required")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        model_chain: Optional[List[str]] = None,
    ) -> str:
        """
        Generate text from a prompt.
        Tries each model in model_chain in order; handles 429 with backoff.

        Returns the generated text string.
        Raises Exception only if ALL models fail.
        """
        chain = model_chain or TEXT_MODEL_CHAIN
        return await self._try_chain(
            chain=chain,
            body=self._text_body(prompt, max_tokens, temperature),
        )

    async def generate_with_image(
        self,
        prompt: str,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        model_chain: Optional[List[str]] = None,
    ) -> str:
        """
        Generate text from a prompt + image (vision).
        Tries each model in model_chain in order; handles 429 with backoff.
        """
        import base64
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        chain = model_chain or VISION_MODEL_CHAIN
        return await self._try_chain(
            chain=chain,
            body=self._vision_body(prompt, image_b64, mime_type, max_tokens, temperature),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _try_chain(self, chain: List[str], body: dict) -> str:
        """Try each model in chain. Retry 429s with backoff before moving on."""
        last_error = None

        for model_name in chain:
            url = f"{GEMINI_V1_BASE}/{model_name}:generateContent?key={self.api_key}"
            try:
                text = await self._call_with_backoff(url, body, model_name)
                logger.info(f"✅ Gemini v1 success with model: {model_name}")
                return text
            except RateLimitError as e:
                logger.warning(f"⚠️ Rate limit exhausted for '{model_name}' after retries, trying next model")
                last_error = e
                continue
            except ModelNotFoundError as e:
                logger.warning(f"⚠️ Model '{model_name}' not found on v1 API, trying next")
                last_error = e
                continue
            except Exception as e:
                logger.warning(f"⚠️ Model '{model_name}' failed: {e}")
                last_error = e
                continue

        raise Exception(f"All Gemini models failed. Last error: {last_error}")

    async def _call_with_backoff(
        self, url: str, body: dict, model_name: str, max_retries: int = 3
    ) -> str:
        """
        Call the Gemini REST endpoint.
        On 429, waits and retries up to max_retries times with exponential backoff.
        Raises RateLimitError if retries are exhausted.
        Raises ModelNotFoundError on 404.
        """
        delay = 5  # initial backoff in seconds

        async with httpx.AsyncClient(timeout=90.0) as client:
            for attempt in range(max_retries + 1):
                response = await client.post(url, json=body)

                if response.status_code == 200:
                    return self._extract_text(response.json(), model_name)

                if response.status_code == 429:
                    if attempt < max_retries:
                        # Try to read retry-after from response
                        wait = delay * (2 ** attempt)
                        try:
                            err_body = response.json()
                            # Gemini 429 body contains retry_delay.seconds
                            retry_seconds = (
                                err_body.get("error", {})
                                .get("details", [{}])[0]
                                .get("retryInfo", {})
                                .get("retryDelay", {})
                                .get("seconds", wait)
                            )
                            wait = min(int(retry_seconds), 30)  # cap at 30s
                        except Exception:
                            pass

                        logger.warning(
                            f"⏳ 429 on '{model_name}' (attempt {attempt + 1}/{max_retries}), "
                            f"waiting {wait}s before retry…"
                        )
                        await asyncio.sleep(wait)
                        continue
                    else:
                        raise RateLimitError(
                            f"429 rate limit exhausted after {max_retries} retries for '{model_name}'"
                        )

                if response.status_code == 404:
                    raise ModelNotFoundError(
                        f"404 model '{model_name}' not found on v1 API"
                    )

                # Any other error — raise immediately
                try:
                    err_msg = response.json().get("error", {}).get("message", response.text)
                except Exception:
                    err_msg = response.text
                raise Exception(f"Gemini API error {response.status_code}: {err_msg}")

        raise Exception("Unexpected exit from retry loop")

    def _extract_text(self, response_json: dict, model_name: str) -> str:
        """Extract text from Gemini v1 response JSON"""
        try:
            candidates = response_json.get("candidates", [])
            if not candidates:
                raise Exception(f"No candidates in response from '{model_name}'")
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise Exception(f"No parts in response from '{model_name}'")
            return parts[0].get("text", "")
        except Exception as e:
            raise Exception(f"Failed to parse Gemini response: {e}\nRaw: {response_json}")

    def _text_body(self, prompt: str, max_tokens: int, temperature: float) -> dict:
        return {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
            },
        }

    def _vision_body(
        self,
        prompt: str,
        image_b64: str,
        mime_type: str,
        max_tokens: int,
        temperature: float,
    ) -> dict:
        return {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inlineData": {"mimeType": mime_type, "data": image_b64}},
                ]
            }],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
            },
        }


# ------------------------------------------------------------------
# Custom exceptions
# ------------------------------------------------------------------

class RateLimitError(Exception):
    """Raised when 429 retries are exhausted for a model"""
    pass


class ModelNotFoundError(Exception):
    """Raised when a model returns 404 on the v1 API"""
    pass