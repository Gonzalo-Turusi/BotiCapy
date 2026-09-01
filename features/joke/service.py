from shared.ai.ai_service import AIService

SYSTEM_PROMPT = (
    "Sos un comediante, breve y ocurrente. "
    "Contás un solo chiste corto (máximo 3 líneas), sin explicaciones extra."
)


class JokeService:
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    async def generar_chiste(self, palabra: str) -> str:
        prompt = f"Hacé un chiste corto que use la palabra '{palabra}'."
        return await self.ai_service.generate(prompt, system_prompt=SYSTEM_PROMPT)
