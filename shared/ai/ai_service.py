from core.logger import logger
from shared.ai.base import AIProvider


class AIService:
    def __init__(self, primary: AIProvider, fallback: AIProvider):
        self._primary = primary
        self._fallback = fallback

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        try:
            logger.info("Attempting to generate with primary provider")
            return await self._primary.generate(prompt, system_prompt)
        except Exception as e:
            logger.warning(f"Primary provider failed: {e}. Falling back to secondary.")
            try:
                return await self._fallback.generate(prompt, system_prompt)
            except Exception as fallback_error:
                logger.error(f"Fallback provider also failed: {fallback_error}")
                raise
