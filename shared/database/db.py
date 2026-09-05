import aiosqlite
from pathlib import Path
from core.logger import logger


DB_PATH = Path(__file__).parent.parent.parent / "boticapy.db"


async def init_db():
    """Initialize the database with the command_states table."""
    async with aiosqlite.connect(str(DB_PATH)) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS command_states (
                name TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                enabled BOOLEAN DEFAULT 1
            )
        """)
        await db.commit()
        logger.info("Database initialized")
