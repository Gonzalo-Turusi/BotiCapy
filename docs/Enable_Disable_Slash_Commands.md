I need to add a global enable/disable system for commands and modules in BotiCapy,
controllable through an HTTP endpoint. Read the existing codebase structure first
(core/, features/, modules/, shared/) before making changes — follow the same
conventions already established (Protocol-based abstractions only where they add
real value, no unnecessary complexity).

Implement the following:

1. SQLite persistence layer in shared/database/:
   - db.py: connection setup using aiosqlite (async, non-blocking)
   - A single table `command_states` with columns: name (TEXT PRIMARY KEY),
     kind (TEXT — either "command" or "module"), enabled (BOOLEAN, default 1)
   - Initialize the DB file on bot startup if it doesn't exist yet

2. shared/registry.py — a CommandRegistry class that:
   - register(name: str, kind: str): inserts the entry into the DB only if it
     doesn't already exist (so re-running the bot doesn't reset manual toggles)
   - is_enabled(name: str) -> bool: checks current state
   - enable(name: str) / disable(name: str): update state in DB
   - list_all() -> list of all registered commands/modules with their state
   - Keep an in-memory cache dict synced with the DB to avoid a DB hit on every
     single command invocation — refresh the cache on enable/disable

3. Auto-registration: in core/bot_client.py's setup_hook, after loading each
   extension from features/ and modules/, register its command(s) in the
   CommandRegistry automatically (kind="command" for slash commands, kind="module"
   for anything in modules/). Use the extension/command name as the registry key.

4. Global enforcement for slash commands: add a check at the bot.tree level
   (interaction_check or a global app_commands.check) that looks up
   CommandRegistry.is_enabled() before any slash command executes. If disabled,
   respond with an ephemeral message like "This command is currently disabled."
   and stop execution — don't let it reach the command's actual logic.

5. Document (as a code comment/docstring) the pattern future modules must follow:
   since modules/ will eventually contain things that listen to channels rather
   than slash commands, each module must manually call
   CommandRegistry.is_enabled("module_name") before acting on any event —
   there's no automatic gateway-level enforcement for those like there is for
   slash commands.

6. New core/api/ package with a FastAPI app (app.py):
   - GET /health — simple liveness check, no auth needed
   - GET /commands — returns the full list from CommandRegistry.list_all()
   - POST /commands/{name}/enable
   - POST /commands/{name}/disable
   - All endpoints except /health require a header `X-API-Key` matching
     ADMIN_API_KEY from config — return 401 if missing or wrong

7. Add ADMIN_API_KEY and ADMIN_API_PORT (default 8000) to core/config.py and
   .env.example. Generate a random secure value as a placeholder example in
   .env.example (not a real key).

8. Wire it up in bot.py: run the FastAPI app via uvicorn.Server programmatically
   as an asyncio task alongside bot.start(), so both run in the same event loop.
   Bind to 127.0.0.1 only (localhost) — this is intentional, not meant to be
   reachable from outside the machine yet.

9. Update requirements.txt with fastapi, uvicorn, and aiosqlite — check PyPI for
   their current latest stable versions, don't assume old ones.

10. When done, give me:
    - the exact curl commands to test each endpoint locally
    - confirmation that /chiste still works normally when enabled, and returns
      the disabled message when I disable it via the endpoint

Rules:
- Don't touch the existing AI layer (shared/ai/) or the joke feature's internal
  logic — only wrap it with the enable/disable check.
- Keep the registry and API code fully decoupled from Discord-specific logic —
  CommandRegistry shouldn't import discord.py types.
- If anything about where a file should live conflicts with the existing
  folder structure rules from BotiCapy_Plan_Scaffold.md, ask before deciding
  on your own.