from groq import AsyncGroq
from core.config import settings
from core.logger import logger
from shared.ai.base import AIProvider


class GroqProvider(AIProvider):
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.groq_api_key)

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=messages,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
