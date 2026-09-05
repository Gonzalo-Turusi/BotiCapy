from fastapi import FastAPI, HTTPException, Header, status
from fastapi.responses import JSONResponse
from core.config import settings
from shared.registry import registry

app = FastAPI(title="BotiCapy Admin API")


async def verify_api_key(x_api_key: str = Header(...)):
    """Verify the API key from the X-API-Key header."""
    if settings.admin_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API key not configured"
        )
    if x_api_key != settings.admin_api_key:
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
async def list_commands(x_api_key: str = Header(...)):
    """Returns the full list of registered commands and modules with their states."""
    await verify_api_key(x_api_key)
    commands = await registry.list_all()
    return {"commands": commands}


@app.post("/commands/{name}/enable")
async def enable_command(name: str, x_api_key: str = Header(...)):
    """Enable a command or module."""
    await verify_api_key(x_api_key)
    await registry.enable(name)
    return {"message": f"Enabled {name}"}


@app.post("/commands/{name}/disable")
async def disable_command(name: str, x_api_key: str = Header(...)):
    """Disable a command or module."""
    await verify_api_key(x_api_key)
    await registry.disable(name)
    return {"message": f"Disabled {name}"}
