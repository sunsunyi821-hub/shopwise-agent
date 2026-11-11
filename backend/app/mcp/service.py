"""Turn raw MCP marketplace results into a ranked, explainable comparison."""

from __future__ import annotations

import math
from typing import Any

from app.mcp.models import (
    MarketplaceProduct,
    MarketplaceSearchResult,
    MarketplaceToolCall,
)

PLATFORM_LABELS = {"jd": "JD", "taobao": "Taobao"}
PLATFORM_ORDER = {"jd": 0, "taobao": 1}


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _format_count(value: int) -> str:
    if value >= 10000:
        return f"{value / 1000:.1f}k"
    return str(value)


def _value_score(
    price: float,
    rating: float,
    review_count: int,
    budget: float,
    matched_count: int,
) -> float:
    """Value score: 40% price, 35% rating, 25% review volume, plus intent matches."""
    price_fit = _clamp(1 - price / budget) if budget > 0 else 0.5
    rating_fit = _clamp((rating - 3.5) / 1.5)
    review_fit = _clamp(math.log10(review_count + 1) / 5)
    base = (0.40 * price_fit + 0.35 * rating_fit + 0.25 * review_fit) * 100
    return round(min(100.0, base + min(matched_count, 3) * 3))


def _matched_tags(product: dict[str, Any], query: str) -> list[str]:
    text = query.lower()
    matched: list[str] = []
    for tag in product.get("tags", []):
        tag_text = str(tag)
        if tag_text.lower() in text or (
            tag_text == "去屑" and ("头屑" in text or "去头皮屑" in text)
        ):
            matched.append(tag_text)
    return matched[:3]


def _reasons(
    product: dict[str, Any],
    *,
    budget_max: float | None,
    query: str,
) -> list[str]:
    reasons = [
        f"Price ¥{float(product['price']):g}"
        + (f", within the ¥{budget_max:g} budget" if budget_max else ""),
        f"Marketplace rating {float(product['rating']):.1f}/5",
        f"{_format_count(int(product['review_count']))} reviews",
    ]
    matched = _matched_tags(product, query)
    if matched:
        reasons.append("Matches: " + ", ".join(matched))
    return reasons


def _to_product(
    raw: dict[str, Any],
    *,
    platform: str,
    budget_max: float | None,
    query: str,
) -> MarketplaceProduct:
    price = float(raw.get("price", 0))
    rating = float(raw.get("rating", 0))
    review_count = int(raw.get("review_count", 0))
    budget = float(budget_max or max(price, 1))
    matched = _matched_tags(raw, query)
    return MarketplaceProduct(
        id=str(raw.get("id", "")),
        platform=platform,
        platform_label=str(
            raw.get("platform_label") or PLATFORM_LABELS.get(platform, platform)
        ),
        name=str(raw.get("name", "")),
        brand=str(raw.get("brand", "")),
        category=str(raw.get("category", "")),
        price=price,
        original_price=raw.get("original_price"),
        rating=rating,
        review_count=review_count,
        sales=int(raw.get("sales", 0)),
        description=str(raw.get("description", "")),
        tags=[str(item) for item in raw.get("tags", [])],
        pros=[str(item) for item in raw.get("pros", [])],
        cons=[str(item) for item in raw.get("cons", [])],
        image_key=str(raw.get("image_key", "")),
        url=str(raw.get("url", "")),
        value_score=_value_score(
            price, rating, review_count, budget, len(matched)
        ),
        reasons=_reasons(raw, budget_max=budget_max, query=query),
    )


def _ensure_platform_diversity(
    products: list[MarketplaceProduct],
    limit: int,
) -> list[MarketplaceProduct]:
    """Keep at least one result per platform so a comparison stays a comparison."""
    top = products[:limit]
    present = {item.platform for item in top}
    for platform in PLATFORM_ORDER:
        if platform in present:
            continue
        replacement = next(
            (item for item in products if item.platform == platform), None
        )
        if replacement is None:
            continue
        if len(top) < limit:
            top.append(replacement)
        else:
            top[-1] = replacement
    return top


def _render_recommendation(
    *,
    query: str,
    products: list[MarketplaceProduct],
    platforms: list[str],
    tool_names: list[str],
    budget_max: float | None,
) -> str:
    platform_text = " / ".join(
        PLATFORM_LABELS.get(item, item) for item in platforms
    )
    if not products:
        return (
            f"### {platform_text} comparison\n\n"
            "No demo products matched the current constraints. "
            "Try a higher budget, another category, or fewer filters."
        )

    lines = [
        f"### {platform_text} comparison",
        "",
        (
            f"> Retrieved with MCP tools {' and '.join(f'`{name}`' for name in tool_names)} "
            f"across {len(platforms)} platform(s). Demo data only; no live transaction API."
        ),
        "",
        "| Rank | Platform | Product | Price | Rating | Reviews | Value |",
        "|---|---|---|---|---|---|---|",
    ]
    for index, item in enumerate(products, start=1):
        name = item.name.replace("|", "/")
        lines.append(
            f"| {index} | {item.platform_label} | {name} | "
            f"¥{item.price:g} | {item.rating:.1f} | "
            f"{_format_count(item.review_count)} | {item.value_score}% |"
        )

    top = products[0]
    lines.extend(
        [
            "",
            f"**Best value: {top.name}** ({top.platform_label}, "
            f"¥{top.price:g}, rating {top.rating:.1f})",
            "",
        ]
    )
    for reason in top.reasons:
        lines.append(f"- {reason}")

    if len(products) > 1:
        cheapest = min(products, key=lambda item: item.price)
        best_rated = max(products, key=lambda item: item.rating)
        most_reviewed = max(products, key=lambda item: item.review_count)
        lines.extend(
            [
                "",
                "**How to choose:**",
                f"- Lowest price: {cheapest.name} ({cheapest.platform_label}, ¥{cheapest.price:g})",
                f"- Highest rating: {best_rated.name} ({best_rated.platform_label}, {best_rated.rating:.1f})",
                f"- Most reviews: {most_reviewed.name} ({most_reviewed.platform_label}, {_format_count(most_reviewed.review_count)})",
            ]
        )

    lines.extend(
        [
            "",
            "Value = 40% price + 35% rating + 25% review volume, "
            "plus a boost for explicit needs"
            + (f"; filtered to the ¥{budget_max:g} budget." if budget_max else "."),
            "External results are for comparison only and cannot be ordered inside ShopWise.",
        ]
    )
    return "\n".join(lines)


def build_marketplace_result(
    *,
    query: str,
    platforms: list[str],
    payloads: list[dict[str, Any]],
    tool_calls: list[dict[str, Any]],
    budget_max: float | None,
    limit: int,
) -> MarketplaceSearchResult:
    products: list[MarketplaceProduct] = []
    seen: set[tuple[str, str]] = set()

    for payload in payloads:
        platform = str(payload.get("platform", "jd"))
        for raw in payload.get("products", []):
            if not isinstance(raw, dict):
                continue
            item = _to_product(
                raw,
                platform=platform,
                budget_max=budget_max,
                query=query,
            )
            if not item.id or not item.name:
                continue
            if budget_max is not None and item.price > float(budget_max):
                continue
            key = (item.platform, item.id)
            if key in seen:
                continue
            seen.add(key)
            products.append(item)

    products.sort(
        key=lambda item: (
            item.value_score,
            item.rating,
            item.review_count,
        ),
        reverse=True,
    )
    limit = max(1, min(5, int(limit or 3)))
    selected = _ensure_platform_diversity(products, limit)
    tool_names = [
        str(call.get("name")) for call in tool_calls if call.get("ok")
    ]
    recommendation = _render_recommendation(
        query=query,
        products=selected,
        platforms=platforms,
        tool_names=tool_names,
        budget_max=budget_max,
    )
    return MarketplaceSearchResult(
        query=query,
        platforms=platforms,
        budget_max=budget_max,
        products=selected,
        recommendation=recommendation,
        tool_calls=[MarketplaceToolCall.model_validate(call) for call in tool_calls],
    )
