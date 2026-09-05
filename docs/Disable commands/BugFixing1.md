There's a critical bug in the command registration logic in core/bot_client.py,
inside the `_load_extensions` method. Fix it and apply three smaller improvements
alongside it.

## Bug (critical, must fix first)

The current code does:

    cog = self.get_cog(feature_dir.name.title())
    if cog:
        for command in cog.get_app_commands():
            await registry.register(command.name, "command")

This guesses the Cog's class name from the folder name (e.g. folder "joke" ->
lookup "Joke"), but the actual class is named "JokeCog" (and future features will
follow the same <Name>Cog convention). get_cog() looks up by exact class name, so
this always returns None, the `if cog:` block never runs, and no command ever gets
registered in the database. The enable/disable system currently does nothing for
real commands.

Fix: remove this per-cog lookup entirely. Instead, after ALL extensions from both
features/ and modules/ have finished loading (i.e. after both the features/ loop
and the modules/ loop complete), do a single pass over the fully-synced command
tree and register every command found there:

    for command in self.tree.walk_commands():
        await registry.register(command.name, "command")

This must not depend on guessing cog class names or folder-name casing in any way,
since it should keep working regardless of how a future feature names its Cog
class. Keep the existing module registration (`await registry.register(module_dir.name, "module")`)
as-is inside the modules/ loop — that part was never guessing a class name and is fine.

## Improvement 1: validate existence in enable/disable endpoints

In core/api/app.py, POST /commands/{name}/enable and /commands/{name}/disable
currently return a 200 success message even if `name` doesn't exist in the
database (the UPDATE just matches zero rows silently). Add an existence check
(or check the affected row count after the UPDATE) and return a 404 with a clear
detail message like "Command or module '{name}' is not registered" when it
doesn't exist.

## Improvement 2: use FastAPI's Depends for auth instead of manual calls

Every route in core/api/app.py currently declares `x_api_key: str = Header(...)`
as a parameter AND separately calls `await verify_api_key(x_api_key)` inside the
function body. Refactor `verify_api_key` to be used purely as a FastAPI dependency
via `Depends(verify_api_key)`, removing the redundant manual call and the extra
Header parameter from each route signature. /health must remain unauthenticated.

## Improvement 3: constant-time API key comparison

In verify_api_key, replace the plain `x_api_key != settings.admin_api_key`
comparison with `secrets.compare_digest(x_api_key, settings.admin_api_key)`
(import `secrets` from the standard library) to avoid a timing side-channel,
even though the practical risk is low given this only binds to localhost.

## Verification

After the fix, walk me through re-testing end to end:
1. Start the bot, confirm in the logs that `chiste` gets registered (add a log
   line if there isn't one already confirming registration count).
2. curl GET /commands and confirm `chiste` appears in the list with enabled: true.
3. curl POST /commands/chiste/disable, then confirm /chiste in Discord returns
   the "disabled" message instead of running.
4. curl POST /commands/does-not-exist/enable and confirm it returns 404.

Don't touch shared/registry.py, shared/database/db.py, or the joke feature's
internal logic — this fix is scoped to core/bot_client.py and core/api/app.py only.