"""External marketplace comparison workflow: MCP search plus value ranking."""

from __future__ import annotations

from typing import Any

from app.mcp.client import MCPMarketplaceClient, detect_platforms
from app.mcp.models import MarketplaceSearchResult
from app.mcp.service import build_marketplace_result


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


async def run_marketplace_search_workflow(
    *,
    client: MCPMarketplaceClient,
    goal: str,
    args: dict[str, Any] | None = None,
) -> MarketplaceSearchResult:
    args = args or {}
    platforms = [
        str(item)
        for item in (args.get("platforms") or detect_platforms(goal))
        if str(item) in {"jd", "taobao"}
    ]
    if not platforms:
        platforms = ["jd", "taobao"]

    query = str(args.get("query") or goal).strip()
    category = str(args["category"]).strip() if args.get("category") else None
    budget_max = _number(args.get("budget_max"))
    limit = int(_number(args.get("limit")) or 3)

    raw = await client.search(
        query=query,
        platforms=platforms,
        category=category,
        budget_max=budget_max,
        limit=limit,
    )
    return build_marketplace_result(
        query=query,
        platforms=raw["platforms"],
        payloads=raw["payloads"],
        tool_calls=raw["tool_calls"],
        budget_max=budget_max,
        limit=limit,
    )
