"""Gemini fallback client for Groq rate-limit events."""

import json
import mimetypes
import os
from pathlib import Path
from typing import Type

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv(".env")


class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured; Gemini fallback is unavailable.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

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
        contents: str | list = user_prompt
        if image_path:
            image = types.Part.from_bytes(
                data=Path(image_path).read_bytes(),
                mime_type=image_mime_type or "image/jpeg",
            )
            contents = [user_prompt, image]

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=4096,
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
        if not response.text:
            raise RuntimeError("Gemini returned an empty structured response")
        return schema.model_validate(json.loads(response.text))

    async def generate_text(self, *, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=4096,
            ),
        )
        return response.text or ""

    async def transcribe_audio(self, file_path: str) -> str:
        mime_type = mimetypes.guess_type(file_path)[0] or "audio/webm"
        audio = types.Part.from_bytes(data=Path(file_path).read_bytes(), mime_type=mime_type)
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=["Transcribe the spoken words accurately. Return only the transcript, without commentary.", audio],
            config=types.GenerateContentConfig(temperature=0, max_output_tokens=4096),
        )
        return response.text or ""
