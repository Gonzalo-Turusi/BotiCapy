from google import genai
from core.config import settings
from core.logger import logger
from shared.ai.base import AIProvider


class GeminiProvider(AIProvider):
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        try:
            if system_prompt:
                response = await self.client.aio.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"{system_prompt}\n\n{prompt}",
                )
            else:
                response = await self.client.aio.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
