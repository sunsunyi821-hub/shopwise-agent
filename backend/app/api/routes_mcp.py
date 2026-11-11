from fastapi import APIRouter, Request

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/tools")
async def list_mcp_tools(request: Request) -> dict:
    """Return the MCP discovery result: transport, server, and discovered tools."""
    client = getattr(request.app.state, "mcp", None)
    if client is None:
        return {
            "enabled": False,
            "available": False,
            "tools": [],
            "error": "MCP client is not initialized",
        }
    return await client.describe()


@router.post("/tools/refresh")
async def refresh_mcp_tools(request: Request) -> dict:
    """Run tools/list again after an MCP server updates its tool catalog."""
    client = getattr(request.app.state, "mcp", None)
    if client is None:
        return {
            "enabled": False,
            "available": False,
            "tools": [],
            "error": "MCP client is not initialized",
        }
    try:
        await client.discover_tools()
    except Exception as exc:  # noqa: BLE001
        return {
            "enabled": client.enabled,
            "available": False,
            "transport": client.transport,
            "server": "shopwise-marketplace",
            "tools": [],
            "error": str(exc),
        }
    return await client.describe()
