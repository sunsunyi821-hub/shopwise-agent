"""ShopWise demo Marketplace MCP Server.

Run it with:
    python -m app.mcp.marketplace_server

It exposes three tools over the standard MCP protocol:
1. search_jd_products: search JD demo listings
2. search_taobao_products: search Taobao/Tmall demo listings
3. get_marketplace_product: read one external product's details

Important: this server uses a fixed, reproducible demo dataset. It does not
scrape JD or Taobao, and it never places a real order or payment. To connect
an official marketplace MCP server, point MCP_MARKETPLACE_URL at it; the
agent-side code does not need to change.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from mcp.server.mcpserver import MCPServer

Platform = Literal["jd", "taobao"]

PLATFORM_LABELS = {"jd": "京东", "taobao": "淘宝"}

MARKETPLACE_PRODUCTS: list[dict[str, Any]] = [
    {
        "id": "jd-1001",
        "platform": "jd",
        "name": "海屿 净屑香氛洗发水 500ml",
        "brand": "海屿",
        "category": "洗发水",
        "price": 89.9,
        "original_price": 119.0,
        "rating": 4.7,
        "review_count": 18642,
        "sales": 32000,
        "description": "针对头屑和头皮异味设计，花香调留香，泡沫细腻，适合油性头皮。",
        "tags": ["去屑", "香气", "花香", "控油", "留香"],
        "pros": ["去屑反馈稳定", "花香调留香久", "泡沫细腻易冲洗"],
        "cons": ["干性发质建议搭配护发素"],
        "image_key": "shampoo",
        "url": "https://example.com/jd/jd-1001",
    },
    {
        "id": "jd-1002",
        "platform": "jd",
        "name": "清岚 去屑止痒洗发露 400ml",
        "brand": "清岚",
        "category": "洗发水",
        "price": 69.0,
        "original_price": 89.0,
        "rating": 4.5,
        "review_count": 9321,
        "sales": 21000,
        "description": "薄荷清爽配方，针对头屑和头皮发痒，清洁力较强。",
        "tags": ["去屑", "止痒", "薄荷", "清爽"],
        "pros": ["止痒反馈快", "价格实惠", "洗后清爽"],
        "cons": ["薄荷感偏强，敏感头皮先试用"],
        "image_key": "shampoo",
        "url": "https://example.com/jd/jd-1002",
    },
    {
        "id": "jd-1003",
        "platform": "jd",
        "name": "沐野 花香去屑洗发水 750ml",
        "brand": "沐野",
        "category": "洗发水",
        "price": 99.0,
        "original_price": 139.0,
        "rating": 4.6,
        "review_count": 3210,
        "sales": 9800,
        "description": "大容量家庭装，去屑同时保留花香，适合长发和家庭囤货。",
        "tags": ["去屑", "花香", "大容量"],
        "pros": ["容量大性价比高", "花香自然", "起泡丰富"],
        "cons": ["香味留存时间中等"],
        "image_key": "shampoo",
        "url": "https://example.com/jd/jd-1003",
    },
    {
        "id": "jd-2001",
        "platform": "jd",
        "name": "初本 神经酰胺修护面霜 50g",
        "brand": "初本",
        "category": "面霜",
        "price": 95.0,
        "original_price": 129.0,
        "rating": 4.8,
        "review_count": 12600,
        "sales": 28000,
        "description": "神经酰胺和角鲨烷复配，主打屏障修护与长效保湿。",
        "tags": ["修护", "保湿", "敏感肌", "屏障"],
        "pros": ["修护反馈稳定", "保湿持久", "质地不厚重"],
        "cons": ["夏季油皮可能觉得偏润"],
        "image_key": "cream",
        "url": "https://example.com/jd/jd-2001",
    },
    {
        "id": "jd-2002",
        "platform": "jd",
        "name": "研白 敏感肌舒缓面霜 40g",
        "brand": "研白",
        "category": "面霜",
        "price": 88.0,
        "original_price": 108.0,
        "rating": 4.6,
        "review_count": 6540,
        "sales": 15400,
        "description": "无香精配方，针对敏感肌泛红和干燥，成分表精简。",
        "tags": ["敏感肌", "舒缓", "无香", "保湿"],
        "pros": ["无香精", "泛红舒缓反馈好", "成分精简"],
        "cons": ["容量偏小"],
        "image_key": "cream",
        "url": "https://example.com/jd/jd-2002",
    },
    {
        "id": "jd-2003",
        "platform": "jd",
        "name": "云栖 高保湿修护霜 50g",
        "brand": "云栖",
        "category": "面霜",
        "price": 129.0,
        "original_price": 159.0,
        "rating": 4.7,
        "review_count": 4320,
        "sales": 7600,
        "description": "高油脂含量，适合干性皮肤和冬季夜间修护。",
        "tags": ["高保湿", "修护", "干皮"],
        "pros": ["极干皮保湿强", "夜间修护感明显"],
        "cons": ["油皮不适合", "价格超过 100 元"],
        "image_key": "cream",
        "url": "https://example.com/jd/jd-2003",
    },
    {
        "id": "jd-3001",
        "platform": "jd",
        "name": "海屿 氨基酸沐浴露 500ml",
        "brand": "海屿",
        "category": "沐浴露",
        "price": 79.0,
        "original_price": 99.0,
        "rating": 4.7,
        "review_count": 15300,
        "sales": 36000,
        "description": "氨基酸表活，无香精，适合敏感肌日常清洁。",
        "tags": ["敏感肌", "无香", "保湿", "氨基酸"],
        "pros": ["温和不紧绷", "无香精", "泡沫细腻"],
        "cons": ["清洁力偏温和，重油汗需多冲洗"],
        "image_key": "bodywash",
        "url": "https://example.com/jd/jd-3001",
    },
    {
        "id": "jd-4001",
        "platform": "jd",
        "name": "清岚 清爽防晒乳 SPF50+ 50ml",
        "brand": "清岚",
        "category": "防晒霜",
        "price": 109.0,
        "original_price": 139.0,
        "rating": 4.6,
        "review_count": 7200,
        "sales": 19000,
        "description": "SPF50+ PA++++，清爽成膜，适合通勤和户外。",
        "tags": ["防晒", "清爽", "SPF50"],
        "pros": ["成膜快", "不泛白", "通勤够用"],
        "cons": ["需要认真卸妆", "价格超过 100 元"],
        "image_key": "sunscreen",
        "url": "https://example.com/jd/jd-4001",
    },
    {
        "id": "tb-1001",
        "platform": "taobao",
        "name": "素造 氨基酸去屑洗发水 500ml",
        "brand": "素造",
        "category": "洗发水",
        "price": 79.0,
        "original_price": 109.0,
        "rating": 4.8,
        "review_count": 56800,
        "sales": 120000,
        "description": "氨基酸表活复配去屑成分，温和清洁，带淡淡花香。",
        "tags": ["去屑", "香气", "花香", "温和", "氨基酸"],
        "pros": ["去屑且温和", "评价数量多", "花香不刺鼻"],
        "cons": ["控油持续时间中等"],
        "image_key": "shampoo",
        "url": "https://example.com/taobao/tb-1001",
    },
    {
        "id": "tb-1002",
        "platform": "taobao",
        "name": "简植 茶香去屑洗发露 450ml",
        "brand": "简植",
        "category": "洗发水",
        "price": 59.9,
        "original_price": 79.9,
        "rating": 4.4,
        "review_count": 21400,
        "sales": 47000,
        "description": "茶香调，主打去屑和控油，价格友好，适合学生党。",
        "tags": ["去屑", "茶香", "控油", "平价"],
        "pros": ["价格低", "控油反馈好", "茶香清爽"],
        "cons": ["去屑强度中等", "干性发质可能偏干"],
        "image_key": "shampoo",
        "url": "https://example.com/taobao/tb-1002",
    },
    {
        "id": "tb-1003",
        "platform": "taobao",
        "name": "清岚 花香去屑洗发水 600ml",
        "brand": "清岚",
        "category": "洗发水",
        "price": 85.0,
        "original_price": 105.0,
        "rating": 4.6,
        "review_count": 8700,
        "sales": 19000,
        "description": "花香去屑配方，600ml 大容量，适合家庭使用。",
        "tags": ["去屑", "花香", "香气", "大容量"],
        "pros": ["香味层次明显", "容量大", "起泡快"],
        "cons": ["泵头偶尔不好按压"],
        "image_key": "shampoo",
        "url": "https://example.com/taobao/tb-1003",
    },
    {
        "id": "tb-2001",
        "platform": "taobao",
        "name": "沐野 敏感肌修护面霜 50g",
        "brand": "沐野",
        "category": "面霜",
        "price": 72.0,
        "original_price": 99.0,
        "rating": 4.7,
        "review_count": 33100,
        "sales": 86000,
        "description": "敏感肌修护配方，无香精，主打保湿和缓解干燥泛红。",
        "tags": ["敏感肌", "修护", "保湿", "无香"],
        "pros": ["价格友好", "敏感肌反馈好", "无香精"],
        "cons": ["修护速度因人而异"],
        "image_key": "cream",
        "url": "https://example.com/taobao/tb-2001",
    },
    {
        "id": "tb-2002",
        "platform": "taobao",
        "name": "海屿 玻尿酸保湿霜 50g",
        "brand": "海屿",
        "category": "面霜",
        "price": 65.0,
        "original_price": 89.0,
        "rating": 4.5,
        "review_count": 18200,
        "sales": 51000,
        "description": "玻尿酸补水，质地清爽，适合春夏和油皮。",
        "tags": ["保湿", "清爽", "玻尿酸", "平价"],
        "pros": ["清爽不黏", "价格低", "上妆不搓泥"],
        "cons": ["冬季干皮保湿不够"],
        "image_key": "cream",
        "url": "https://example.com/taobao/tb-2002",
    },
    {
        "id": "tb-2003",
        "platform": "taobao",
        "name": "初本 屏障修护霜 45g",
        "brand": "初本",
        "category": "面霜",
        "price": 118.0,
        "original_price": 148.0,
        "rating": 4.9,
        "review_count": 7200,
        "sales": 16000,
        "description": "高浓度神经酰胺，针对屏障受损和反复泛红。",
        "tags": ["修护", "敏感肌", "屏障", "保湿"],
        "pros": ["评分高", "修护成分浓度高"],
        "cons": ["价格超过 100 元", "容量偏小"],
        "image_key": "cream",
        "url": "https://example.com/taobao/tb-2003",
    },
    {
        "id": "tb-3001",
        "platform": "taobao",
        "name": "简植 无香氨基酸沐浴露 500ml",
        "brand": "简植",
        "category": "沐浴露",
        "price": 59.0,
        "original_price": 79.0,
        "rating": 4.6,
        "review_count": 27600,
        "sales": 73000,
        "description": "无香精氨基酸配方，适合敏感肌和不喜欢香味的用户。",
        "tags": ["敏感肌", "无香", "氨基酸", "保湿"],
        "pros": ["无香", "价格低", "洗后不紧绷"],
        "cons": ["泡沫比皂基少"],
        "image_key": "bodywash",
        "url": "https://example.com/taobao/tb-3001",
    },
    {
        "id": "tb-4001",
        "platform": "taobao",
        "name": "素造 轻透防晒乳 SPF50 50ml",
        "brand": "素造",
        "category": "防晒霜",
        "price": 89.0,
        "original_price": 119.0,
        "rating": 4.5,
        "review_count": 19300,
        "sales": 44000,
        "description": "轻透不黏，SPF50，适合日常通勤。",
        "tags": ["防晒", "清爽", "SPF50"],
        "pros": ["价格友好", "清爽不闷", "不泛白"],
        "cons": ["户外暴晒需要补涂"],
        "image_key": "sunscreen",
        "url": "https://example.com/taobao/tb-4001",
    },
]

DOMAIN_TERMS = [
    "洗发水",
    "沐浴露",
    "面霜",
    "护肤霜",
    "防晒",
    "去屑",
    "去头皮屑",
    "头皮屑",
    "香气",
    "花香",
    "茶香",
    "薄荷",
    "控油",
    "止痒",
    "保湿",
    "修护",
    "敏感肌",
    "无香",
    "清爽",
    "温和",
    "平价",
    "大容量",
    "屏障",
    "玻尿酸",
    "氨基酸",
    "SPF50",
]

TERM_SYNONYMS = {
    "去头皮屑": "去屑",
    "头皮屑": "去屑",
    "有香气": "香气",
    "香味": "香气",
    "护肤霜": "面霜",
    "防晒乳": "防晒",
    "防晒霜": "防晒",
}


def _normalize_term(term: str) -> str:
    term = term.strip().lower()
    return TERM_SYNONYMS.get(term, TERM_SYNONYMS.get(term.replace("有", ""), term))


def _query_terms(query: str, category: str | None) -> list[str]:
    """Extract demo-domain keywords without depending on an external tokenizer."""
    text = query.lower()
    terms = [term for term in DOMAIN_TERMS if term.lower() in text]
    if category:
        terms.append(category)
    for raw in re.split(r"[\s,，。；;、]+", text):
        if len(raw) >= 2:
            terms.append(_normalize_term(raw))
    return list(dict.fromkeys(term for term in terms if term))


def _search(
    platform: Platform,
    query: str,
    category: str | None,
    budget_max: float | None,
    limit: int,
) -> dict[str, Any]:
    limit = max(1, min(5, int(limit or 5)))
    terms = _query_terms(query, category)
    candidates: list[tuple[int, dict[str, Any]]] = []

    for product in MARKETPLACE_PRODUCTS:
        if product["platform"] != platform:
            continue
        if category and product["category"] != category:
            continue
        if budget_max is not None and product["price"] > float(budget_max):
            continue

        searchable = " ".join(
            [
                product["name"],
                product["brand"],
                product["category"],
                product["description"],
                " ".join(product["tags"]),
                " ".join(product["pros"]),
            ]
        ).lower()
        hits = 0
        for term in terms:
            normalized = _normalize_term(term)
            if normalized and normalized.lower() in searchable:
                hits += 1
        candidates.append((hits, product))

    positive = [item for item in candidates if item[0] > 0]
    pool = positive or candidates
    pool.sort(
        key=lambda item: (
            item[0],
            item[1]["rating"],
            item[1]["review_count"],
        ),
        reverse=True,
    )

    products = [dict(item[1]) for item in pool[:limit]]
    return {
        "platform": platform,
        "platform_label": PLATFORM_LABELS[platform],
        "query": query,
        "category": category,
        "budget_max": budget_max,
        "total": len(products),
        "products": products,
        "note": "Demo data; not a live JD or Taobao price.",
    }


mcp = MCPServer(
    "shopwise-marketplace",
    title="ShopWise Marketplace MCP",
    version="1.0.0",
    instructions=(
        "Search JD and Taobao demo listings and read product details. "
        "All data is fixed demo data; no live pages, orders, or payments."
    ),
    log_level="WARNING",
)


@mcp.tool()
async def search_jd_products(
    query: str,
    category: str | None = None,
    budget_max: float | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Search JD demo products by category and budget; return price, rating, reviews, and highlights."""
    return _search("jd", query, category, budget_max, limit)


@mcp.tool()
async def search_taobao_products(
    query: str,
    category: str | None = None,
    budget_max: float | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Search Taobao/Tmall demo products by category and budget; return price, rating, reviews, and highlights."""
    return _search("taobao", query, category, budget_max, limit)


@mcp.tool()
async def get_marketplace_product(platform: Platform, product_id: str) -> dict[str, Any]:
    """Read the full details of one demo product by platform and product ID."""
    for product in MARKETPLACE_PRODUCTS:
        if product["platform"] == platform and product["id"] == product_id:
            return {
                "platform": platform,
                "platform_label": PLATFORM_LABELS[platform],
                "product": dict(product),
            }
    return {"error": f"Product not found: {platform}/{product_id}"}


if __name__ == "__main__":
    mcp.run(transport="stdio")
