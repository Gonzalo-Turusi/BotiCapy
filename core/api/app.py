import secrets
from fastapi import FastAPI, HTTPException, Header, status, Depends
from fastapi.responses import JSONResponse
from core.config import settings
from shared.registry import registry

app = FastAPI(title="BotiCapy Admin API")


async def verify_api_key(x_api_key: str = Header(...)):
    """Verify the API key from the X-API-Key header using constant-time comparison."""
    if settings.admin_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API key not configured"
        )
    if not secrets.compare_digest(x_api_key, settings.admin_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return x_api_key


@app.get("/health")
async def health_check():
    """Simple liveness check, no auth needed."""
    return {"status": "healthy"}


@app.get("/commands")
async def list_commands(api_key: str = Depends(verify_api_key)):
    """Returns the full list of registered commands and modules with their states."""
    commands = await registry.list_all()
    return {"commands": commands}


@app.post("/commands/{name}/enable")
async def enable_command(name: str, api_key: str = Depends(verify_api_key)):
    """Enable a command or module."""
    # Check if command/module exists
    commands = await registry.list_all()
    exists = any(cmd["name"] == name for cmd in commands)
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Command or module '{name}' is not registered"
        )
    await registry.enable(name)
    return {"message": f"Enabled {name}"}


@app.post("/commands/{name}/disable")
async def disable_command(name: str, api_key: str = Depends(verify_api_key)):
    """Disable a command or module."""
    # Check if command/module exists
    commands = await registry.list_all()
    exists = any(cmd["name"] == name for cmd in commands)
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Command or module '{name}' is not registered"
        )
    await registry.disable(name)
    return {"message": f"Disabled {name}"}
