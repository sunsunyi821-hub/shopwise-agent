"""MCP client used by the agent's marketplace workflow.

The agent never imports the demo marketplace catalog. It discovers tools with
MCP `tools/list` and invokes them with `tools/call`. By default the client
launches `app.mcp.marketplace_server` over stdio; setting
MCP_MARKETPLACE_URL connects to a remote Streamable HTTP MCP server instead.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from typing import Any

from mcp import Client
from mcp.client.stdio import StdioServerParameters

from app.config import BACKEND_DIR, Settings

logger = logging.getLogger(__name__)

PLATFORM_LABELS = {"jd": "JD", "taobao": "Taobao"}
PLATFORM_HINTS = {
    "jd": ("jd", "京东"),
    "taobao": ("taobao", "淘宝", "天猫"),
}
KNOWN_PLATFORMS = tuple(PLATFORM_LABELS)


class MCPUnavailableError(RuntimeError):
    pass


class MCPToolError(RuntimeError):
    pass


def detect_platforms(text: str) -> list[str]:
    """Detect external platforms mentioned in a user goal."""
    lowered = text.lower()
    platforms: list[str] = []
    for platform, hints in PLATFORM_HINTS.items():
        if any(hint in lowered for hint in hints):
            platforms.append(platform)
    return platforms


def _tool_payload(result: Any) -> dict[str, Any]:
    """Accept both structured and text-only MCP tool results."""
    if getattr(result, "is_error", None):
        text = " ".join(
            getattr(item, "text", "") for item in getattr(result, "content", [])
        ).strip()
        raise MCPToolError(text or "MCP tool returned an error")

    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        if set(structured) == {"result"}:
            value = structured["result"]
            return value if isinstance(value, dict) else {"value": value}
        return structured

    for item in getattr(result, "content", []):
        text = getattr(item, "text", None)
        if not text:
            continue
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise MCPToolError("MCP tool did not return parseable structured data")


class MCPMarketplaceClient:
    """MCP client specialized for marketplace search tools."""

    def __init__(self, settings: Settings, *, inprocess: bool | None = None) -> None:
        self.settings = settings
        self.enabled = bool(settings.mcp_enabled)
        self.inprocess = (
            settings.mcp_marketplace_inprocess if inprocess is None else inprocess
        )
        self.url = settings.mcp_marketplace_url
        self.timeout = settings.mcp_marketplace_timeout_seconds
        self._tools: list[dict[str, Any]] = []
        self._discovery_error: str | None = None

    @property
    def transport(self) -> str:
        if self.inprocess:
            return "inprocess"
        return "streamable-http" if self.url else "stdio"

    def _server_spec(self) -> Any:
        if self.inprocess:
            from app.mcp.marketplace_server import mcp

            return mcp
        if self.url:
            return self.url
        command = self.settings.mcp_marketplace_command or sys.executable
        return StdioServerParameters(
            command=command,
            args=["-m", "app.mcp.marketplace_server"],
            cwd=BACKEND_DIR,
            env={"PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"},
        )

    def _make_client(self) -> Client:
        return Client(
            self._server_spec(),
            read_timeout_seconds=self.timeout,
            cache=None,
        )

    @staticmethod
    def _tool_info(tool: Any) -> dict[str, Any]:
        return {
            "name": getattr(tool, "name", ""),
            "description": getattr(tool, "description", "") or "",
            "input_schema": getattr(tool, "input_schema", None)
            or getattr(tool, "inputSchema", None)
            or {},
        }

    async def _list_tools(self, client: Client) -> list[dict[str, Any]]:
        result = await client.list_tools()
        tools = [self._tool_info(tool) for tool in result.tools]
        if tools:
            self._tools = tools
            self._discovery_error = None
        return tools

    async def discover_tools(self) -> list[dict[str, Any]]:
        """Connect to the MCP server and cache the tools/list result."""
        if not self.enabled:
            return []
        try:
            async with asyncio.timeout(self.timeout):
                async with self._make_client() as client:
                    return await self._list_tools(client)
        except Exception as exc:  # noqa: BLE001
            self._discovery_error = str(exc)
            logger.warning("MCP tool discovery failed: %s", exc)
            raise

    def _platform_tool(
        self,
        platform: str,
        tools: list[dict[str, Any]],
    ) -> tuple[str, bool] | None:
        """Map a platform to a discovered tool and flag generic search tools."""
        hints = PLATFORM_HINTS[platform]
        preferred = f"search_{platform}_products"
        by_name = {tool["name"]: tool for tool in tools}
        if preferred in by_name:
            return preferred, False
        for name in by_name:
            lowered = name.lower()
            if any(hint in lowered for hint in hints) and "search" in lowered:
                return name, False
        for name in by_name:
            if name in {"search_products", "marketplace_search"}:
                return name, True
        return None

    async def search(
        self,
        *,
        query: str,
        platforms: list[str],
        category: str | None = None,
        budget_max: float | None = None,
        limit: int = 3,
    ) -> dict[str, Any]:
        """Call multiple platform search tools through one MCP connection."""
        if not self.enabled:
            raise MCPUnavailableError("MCP is disabled")
        selected = [item for item in platforms if item in KNOWN_PLATFORMS]
        if not selected:
            selected = ["jd", "taobao"]

        payloads: list[dict[str, Any]] = []
        calls: list[dict[str, Any]] = []

        try:
            async with asyncio.timeout(self.timeout):
                async with self._make_client() as client:
                    tools = self._tools or await self._list_tools(client)
                    for platform in selected:
                        mapping = self._platform_tool(platform, tools)
                        if mapping is None:
                            calls.append(
                                {
                                    "name": f"search_{platform}_products",
                                    "arguments": {},
                                    "ok": False,
                                    "error": "MCP server does not expose a search tool for this platform",
                                }
                            )
                            continue
                        tool_name, generic = mapping
                        arguments: dict[str, Any] = {"query": query}
                        if generic:
                            arguments["platform"] = platform
                        if category:
                            arguments["category"] = category
                        if budget_max is not None:
                            arguments["budget_max"] = float(budget_max)
                        arguments["limit"] = max(1, min(5, int(limit)))

                        started = time.perf_counter()
                        try:
                            result = await client.call_tool(tool_name, arguments)
                            payload = _tool_payload(result)
                        except Exception as exc:  # noqa: BLE001
                            calls.append(
                                {
                                    "name": tool_name,
                                    "arguments": arguments,
                                    "ok": False,
                                    "duration_ms": int(
                                        (time.perf_counter() - started) * 1000
                                    ),
                                    "error": str(exc),
                                }
                            )
                            continue

                        calls.append(
                            {
                                "name": tool_name,
                                "arguments": arguments,
                                "ok": True,
                                "duration_ms": int(
                                    (time.perf_counter() - started) * 1000
                                ),
                            }
                        )
                        payload.setdefault("platform", platform)
                        payload.setdefault(
                            "platform_label", PLATFORM_LABELS.get(platform, platform)
                        )
                        payloads.append(payload)
        except TimeoutError as exc:
            raise MCPUnavailableError("MCP tool call timed out") from exc
        except MCPToolError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise MCPUnavailableError(f"MCP connection failed: {exc}") from exc

        if not payloads:
            detail = "; ".join(
                call.get("error", "") for call in calls if not call.get("ok")
            )
            raise MCPToolError(detail or "No external marketplace results")

        return {"platforms": selected, "payloads": payloads, "tool_calls": calls}

    async def describe(self, *, refresh: bool = False) -> dict[str, Any]:
        """Expose discovery status for GET /api/mcp/tools."""
        base = {
            "enabled": self.enabled,
            "transport": self.transport,
            "server": "shopwise-marketplace",
        }
        if not self.enabled:
            return {**base, "available": False, "tools": [], "error": "MCP is disabled"}
        if not refresh and self._tools:
            return {**base, "available": True, "tools": self._tools, "error": None}
        try:
            tools = await self.discover_tools()
        except Exception as exc:  # noqa: BLE001
            return {
                **base,
                "available": False,
                "tools": [],
                "error": str(exc) or self._discovery_error,
            }
        return {**base, "available": True, "tools": tools, "error": None}
