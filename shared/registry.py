from typing import Dict, List
import aiosqlite
from shared.database.db import DB_PATH
from core.logger import logger


class CommandRegistry:
    """Registry for managing command and module enable/disable states.
    
    This class maintains an in-memory cache of command states to avoid
    database hits on every command invocation. The cache is refreshed
    whenever states are modified.
    
    Future modules that listen to channels (rather than slash commands)
    must manually call CommandRegistry.is_enabled("module_name") before
    acting on any event, as there is no automatic gateway-level enforcement
    for those like there is for slash commands.
    """
    
    def __init__(self):
        self._cache: Dict[str, bool] = {}
    
    async def _refresh_cache(self):
        """Refresh the in-memory cache from the database."""
        async with aiosqlite.connect(str(DB_PATH)) as db:
            cursor = await db.execute("SELECT name, enabled FROM command_states")
            rows = await cursor.fetchall()
            self._cache = {row[0]: bool(row[1]) for row in rows}
            logger.debug(f"Refreshed registry cache with {len(self._cache)} entries")
    
    async def register(self, name: str, kind: str):
        """Register a command or module in the database if it doesn't exist.
        
        Args:
            name: The name of the command or module
            kind: Either "command" or "module"
        """
        async with aiosqlite.connect(str(DB_PATH)) as db:
            # Check if already exists
            cursor = await db.execute(
                "SELECT name FROM command_states WHERE name = ?",
                (name,)
            )
            existing = await cursor.fetchone()
            
            if existing is None:
                await db.execute(
                    "INSERT INTO command_states (name, kind, enabled) VALUES (?, ?, 1)",
                    (name, kind)
                )
                await db.commit()
                self._cache[name] = True
                logger.info(f"Registered new {kind}: {name}")
            else:
                # Ensure cache is up to date for existing entries
                cursor = await db.execute(
                    "SELECT enabled FROM command_states WHERE name = ?",
                    (name,)
                )
                row = await cursor.fetchone()
                self._cache[name] = bool(row[0])
    
    async def is_enabled(self, name: str) -> bool:
        """Check if a command or module is enabled.
        
        Args:
            name: The name of the command or module
            
        Returns:
            True if enabled, False otherwise
        """
        if name not in self._cache:
            # If not in cache, try to load from DB
            async with aiosqlite.connect(str(DB_PATH)) as db:
                cursor = await db.execute(
                    "SELECT enabled FROM command_states WHERE name = ?",
                    (name,)
                )
                row = await cursor.fetchone()
                if row:
                    self._cache[name] = bool(row[0])
                    return self._cache[name]
                else:
                    # Not registered, assume enabled by default
                    logger.warning(f"Unregistered command/module: {name}, assuming enabled")
                    return True
        
        return self._cache[name]
    
    async def enable(self, name: str):
        """Enable a command or module.
        
        Args:
            name: The name of the command or module
        """
        async with aiosqlite.connect(str(DB_PATH)) as db:
            await db.execute(
                "UPDATE command_states SET enabled = 1 WHERE name = ?",
                (name,)
            )
            await db.commit()
            self._cache[name] = True
            logger.info(f"Enabled: {name}")
    
    async def disable(self, name: str):
        """Disable a command or module.
        
        Args:
            name: The name of the command or module
        """
        async with aiosqlite.connect(str(DB_PATH)) as db:
            await db.execute(
                "UPDATE command_states SET enabled = 0 WHERE name = ?",
                (name,)
            )
            await db.commit()
            self._cache[name] = False
            logger.info(f"Disabled: {name}")
    
    async def list_all(self) -> List[Dict[str, any]]:
        """List all registered commands and modules with their states.
        
        Returns:
            A list of dictionaries containing name, kind, and enabled status
        """
        async with aiosqlite.connect(str(DB_PATH)) as db:
            cursor = await db.execute("SELECT name, kind, enabled FROM command_states")
            rows = await cursor.fetchall()
            return [
                {
                    "name": row[0],
                    "kind": row[1],
                    "enabled": bool(row[2])
                }
                for row in rows
            ]


# Global registry instance
registry = CommandRegistry()
