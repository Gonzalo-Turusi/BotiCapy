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
from shared.database.db import init_db
from shared.registry import registry


class BotiCapyClient(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.ai_service: AIService | None = None

    async def setup_hook(self):
        logger.info("Setting up bot...")

        # Initialize database
        await init_db()

        # Instantiate AI service with Groq as primary, Gemini as fallback
        primary = GroqProvider()
        fallback = GeminiProvider()
        self.ai_service = AIService(primary, fallback)
        logger.info("AI service initialized")

        # Auto-load all extensions from features/ and modules/
        await self._load_extensions()

        # Setup global error handler
        setup_error_handler(self)

        # Setup global command check for enable/disable
        self.tree.interaction_check = self._global_interaction_check

        logger.info("Bot setup complete")

    async def _global_interaction_check(self, interaction: discord.Interaction) -> bool:
        """Global check to enforce enable/disable for all slash commands."""
        command_name = interaction.command.name if interaction.command else None
        if command_name:
            is_enabled = await registry.is_enabled(command_name)
            if not is_enabled:
                await interaction.response.send_message(
                    "This command is currently disabled.",
                    ephemeral=True
                )
                return False
        return True

    async def _load_extensions(self):
        """Dynamically load all Cogs from features/ and modules/ directories and register their commands."""
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
                        
                        # Register the module itself
                        await registry.register(module_dir.name, "module")
                        logger.info(f"Registered module: {module_dir.name}")
                    except Exception as e:
                        logger.error(f"Failed to load extension {extension_path}: {e}")

        # Register all slash commands from the fully-synced command tree
        command_count = 0
        for command in self.tree.walk_commands():
            await registry.register(command.name, "command")
            command_count += 1
        logger.info(f"Registered {command_count} commands from command tree")
