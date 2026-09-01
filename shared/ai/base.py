from typing import Protocol


class AIProvider(Protocol):
    """Contract that any AI provider must implement."""

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        ...
