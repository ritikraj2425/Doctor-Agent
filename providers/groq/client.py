import base64
import json
import logging
import os
from pathlib import Path
from typing import Type

from dotenv import load_dotenv
from groq import AsyncGroq
from pydantic import BaseModel

load_dotenv(".env")
logger = logging.getLogger(__name__)


class ProviderFallbackError(RuntimeError):
    """Groq was rate-limited and the configured Gemini fallback also failed."""

    def __init__(self, public_message: str):
        super().__init__(public_message)
        self.public_message = public_message


class GroqClient:
    """Groq chat and transcription client used by all model-backed agent nodes."""

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set.")
        self.client = AsyncGroq(api_key=api_key, timeout=60.0)
        self.model_name = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
        self.last_provider = "groq"

    @staticmethod
    def _is_rate_limited(error: Exception) -> bool:
        if getattr(error, "status_code", None) == 429:
            return True
        body = getattr(error, "body", None) or {}
        detail = body.get("error") if isinstance(body, dict) else None
        return isinstance(detail, dict) and detail.get("code") == "rate_limit_exceeded"

    @staticmethod
    def _fallback_error(error: Exception) -> ProviderFallbackError:
        code = getattr(error, "code", None) or getattr(error, "status_code", None)
        if code == 403 or "403" in str(error):
            reason = "Gemini rejected the request (HTTP 403). Enable Gemini API billing/access for the configured Google project."
        elif code == 429 or "429" in str(error):
            reason = "Gemini also reached its rate limit. Wait for its quota window to reset or check Gemini billing and quotas."
        elif isinstance(error, ValueError) and "GEMINI_API_KEY" in str(error):
            reason = "GEMINI_API_KEY is missing from the running server environment."
        else:
            reason = f"Gemini fallback failed ({error.__class__.__name__}). Check the server log for details."
        return ProviderFallbackError(f"Groq was rate-limited and the Gemini fallback failed. {reason}")

    @staticmethod
    def _strict_schema(model: Type[BaseModel]) -> dict:
        schema = model.model_json_schema()

        def normalize(node):
            if isinstance(node, dict):
                if node.get("type") == "object" or "properties" in node:
                    props = node.get("properties", {})
                    node["required"] = list(props.keys())
                    node["additionalProperties"] = False
                for value in node.values():
                    normalize(value)
            elif isinstance(node, list):
                for value in node:
                    normalize(value)
        normalize(schema)
        return schema

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: Type[BaseModel],
        temperature: float = 0.2,
        image_path: str | None = None,
        image_mime_type: str | None = None,
    ):
        user_content: str | list[dict] = user_prompt
        if image_path:
            mime = image_mime_type or "image/jpeg"
            encoded = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
            user_content = [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}},
            ]

        schema_json = json.dumps(schema.model_json_schema(), ensure_ascii=False)
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt + "\nReturn only a valid JSON object matching this schema. Every listed field must be present; use null or an empty list where appropriate.\nJSON schema: " + schema_json},
                    {"role": "user", "content": user_content},
                ],
                temperature=temperature,
                max_completion_tokens=4096,
                response_format={"type": "json_object"},
            )
        except Exception as groq_error:
            if not self._is_rate_limited(groq_error):
                raise
            try:
                from providers.gemini.client import GeminiClient
                logger.info("Groq rate limit reached; retrying structured request with Gemini")
                result = await GeminiClient().generate_structured(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    schema=schema,
                    temperature=temperature,
                    image_path=image_path,
                    image_mime_type=image_mime_type,
                )
            except Exception as gemini_error:
                logger.warning("Groq rate limit reached and Gemini fallback failed", exc_info=gemini_error)
                raise self._fallback_error(gemini_error) from gemini_error
            self.last_provider = "gemini"
            return result
        self.last_provider = "groq"
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("Groq returned an empty structured response")
        return schema.model_validate(json.loads(content))

    async def generate_text(self, *, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=temperature,
                max_completion_tokens=4096,
            )
        except Exception as groq_error:
            if not self._is_rate_limited(groq_error):
                raise
            try:
                from providers.gemini.client import GeminiClient
                logger.info("Groq rate limit reached; retrying text request with Gemini")
                result = await GeminiClient().generate_text(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=temperature,
                )
            except Exception as gemini_error:
                logger.warning("Groq rate limit reached and Gemini fallback failed", exc_info=gemini_error)
                raise self._fallback_error(gemini_error) from gemini_error
            self.last_provider = "gemini"
            return result
        self.last_provider = "groq"
        return response.choices[0].message.content or ""
