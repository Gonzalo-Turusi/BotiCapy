import os
from pathlib import Path
import discord
from discord.ext import commands
from core.config import settings
from core.logger import logger
from core.errors import setup_error_handler
from shared.ai.groq_provider import GroqProvider
from shared.ai.gemini_provider import GeminiProvider
from shared.ai.ai_service import AIService


class BotiCapyClient(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.ai_service: AIService | None = None

    async def setup_hook(self):
        logger.info("Setting up bot...")

        # Instantiate AI service with Groq as primary, Gemini as fallback
        primary = GroqProvider()
        fallback = GeminiProvider()
        self.ai_service = AIService(primary, fallback)
        logger.info("AI service initialized")

        # Auto-load all extensions from features/ and modules/
        await self._load_extensions()

        # Setup global error handler
        setup_error_handler(self)

        logger.info("Bot setup complete")

    async def _load_extensions(self):
        """Dynamically load all Cogs from features/ and modules/ directories."""
        base_path = Path(__file__).parent.parent

        # Load from features/
        features_path = base_path / "features"
        if features_path.exists():
            for feature_dir in features_path.iterdir():
                if feature_dir.is_dir() and not feature_dir.name.startswith("_"):
                    extension_path = f"features.{feature_dir.name}.commands"
                    try:
                        await self.load_extension(extension_path)
                        logger.info(f"Loaded extension: {extension_path}")
                    except Exception as e:
                        logger.error(f"Failed to load extension {extension_path}: {e}")

        # Load from modules/
        modules_path = base_path / "modules"
        if modules_path.exists():
            for module_dir in modules_path.iterdir():
                if module_dir.is_dir() and not module_dir.name.startswith("_"):
                    extension_path = f"modules.{module_dir.name}.commands"
                    try:
                        await self.load_extension(extension_path)
                        logger.info(f"Loaded extension: {extension_path}")
                    except Exception as e:
                        logger.error(f"Failed to load extension {extension_path}: {e}")
