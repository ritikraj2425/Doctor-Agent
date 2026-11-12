import asyncio
import os
import re
from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv(".env")


class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    async def generate_content(
        self,
        contents,
        config=None,
        model=None,
        max_retries: int = 4,
    ):
        """
        Wrapper around client.aio.models.generate_content with built-in
        exponential backoff / quota retry handling for 429 RESOURCE_EXHAUSTED.
        """
        target_model = model or self.model_name

        for attempt in range(max_retries):
            try:
                return await self.client.aio.models.generate_content(
                    model=target_model,
                    contents=contents,
                    config=config,
                )
            except errors.ClientError as e:
                is_rate_limited = "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
                if is_rate_limited and attempt < max_retries - 1:
                    match = re.search(r"retry in (\d+(\.\d+)?)s", str(e))
                    delay = float(match.group(1)) + 1.0 if match else 15.0 * (attempt + 1)
                    print(
                        f"[GeminiClient] Rate limit hit (429). Retrying in {delay:.1f}s "
                        f"(attempt {attempt + 1}/{max_retries})..."
                    )
                    await asyncio.sleep(delay)
                    continue
                raise
