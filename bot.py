import asyncio
from dotenv import load_dotenv
from core.config import settings
from core.logger import logger
from core.bot_client import BotiCapyClient
from core.api.app import app
import uvicorn


async def main():
    load_dotenv()
    logger.info("Starting BotiCapy...")

    bot = BotiCapyClient()

    @bot.event
    async def on_ready():
        logger.info(f"Logged in as {bot.user}")
        # Sync slash commands globally
        try:
            synced = await bot.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    # Configure uvicorn to run the FastAPI app
    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=settings.admin_api_port,
        log_level="info"
    )
    server = uvicorn.Server(config)

    # Run both bot and API server concurrently
    await asyncio.gather(
        bot.start(settings.discord_token),
        server.serve()
    )


if __name__ == "__main__":
    asyncio.run(main())
