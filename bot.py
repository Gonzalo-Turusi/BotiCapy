from dotenv import load_dotenv
from core.config import settings
from core.logger import logger
from core.bot_client import BotiCapyClient


def main():
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


    bot.run(settings.discord_token)


if __name__ == "__main__":
    main()
