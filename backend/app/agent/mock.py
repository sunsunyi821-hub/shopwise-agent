import asyncio
import re
from collections.abc import AsyncIterator

from app.agent.state import (
    RecommendationContext,
    ReviewAnalysis,
    ShoppingIntent,
    ShoppingProfile,
)

CATEGORY_SYNONYMS: dict[str, list[str]] = {
    "沐浴露": ["沐浴露", "沐浴乳", "沐浴液", "洗澡"],
    "洗发水": ["洗发水", "洗发露", "洗发液", "洗头"],
    "面霜": ["面霜", "面乳", "保湿霜", "修护霜"],
    "防晒霜": ["防晒霜", "防晒乳", "防晒"],
    "牙膏": ["牙膏", "刷牙"],
    "洗衣液": ["洗衣液", "洗衣服", "洗衣"],
}

KNOWN_BRANDS = ["清岚", "沐野", "简植", "海屿", "初本", "研白", "云栖", "素造"]

SKIN_TYPES = {
    "敏感肌": "敏感肌",
    "敏感": "敏感肌",
    "干皮": "干性",
    "干性": "干性",
    "油皮": "油性",
    "油性": "油性",
    "混合": "混合性",
    "中性": "中性",
}

SCENTS = {
    "无香": "无香",
    "没有香味": "无香",
    "不含香精": "无香",
    "无香味": "无香",
    "花香": "花香",
    "柑橘": "柑橘",
    "木质": "木质",
    "果香": "果香",
}

FUNCTIONS = [
    "控油",
    "去屑",
    "保湿",
    "修护",
    "美白",
    "抗敏",
    "除菌",
    "留香",
    "蓬松",
    "清爽",
    "滋润",
]

POSITIVE_HINTS = (
    "好",
    "喜欢",
    "满意",
    "推荐",
    "舒服",
    "温和",
    "清爽",
    "有效",
    "惊喜",
    "回购",
    "不错",
)

NEGATIVE_HINTS = (
    "差",
    "失望",
    "刺激",
    "干",
    "贵",
    "难用",
    "过敏",
    "不好",
    "油腻",
    "假滑",
)

REVIEW_TAG_HINTS = {
    "敏感肌": "敏感肌",
    "香": "香味",
    "味": "香味",
    "保湿": "保湿",
    "控油": "控油",
    "清爽": "清爽",
    "油腻": "清爽",
    "价格": "价格",
    "贵": "价格",
    "便宜": "价格",
    "包装": "包装",
    "物流": "物流",
    "泡沫": "泡沫",
    "回购": "回购",
}

def _has_hint(sentence: str, hints: tuple[str, ...]) -> bool:
    """Match a hint word while skipping negated forms such as 不刺激 or 没有刺激."""
    for word in hints:
        for match in re.finditer(re.escape(word), sentence):
            prefix = sentence[max(0, match.start() - 2) : match.start()]
            if not any(negation in prefix for negation in ("不", "没", "无", "别")):
                return True
    return False


BUDGET_PATTERNS = [
    r"预算\s*(?:是|为|在|大概|约)?\s*(\d+(?:\.\d+)?)",
    r"(\d+(?:\.\d+)?)\s*(?:元|块|rmb|¥)?\s*(?:以内|以下|之内|封顶)",
    r"不超过\s*(\d+(?:\.\d+)?)",
    r"(\d+(?:\.\d+)?)\s*(?:元|块)\s*(?:左右|上下)",
]

RATING_PATTERN = r"(\d(?:\.\d)?)\s*分(?:以上|及以上|\+)"
EXCLUDE_PATTERN = r"(?:不要|不含|排除|避开)(?:含|有)?([一-龥A-Za-z0-9]{2,8})"


def _find_category(message: str) -> str | None:
    for category, synonyms in CATEGORY_SYNONYMS.items():
        if any(synonym in message for synonym in synonyms):
            return category
    return None


def _find_budget(message: str) -> float | None:
    for pattern in BUDGET_PATTERNS:
        match = re.search(pattern, message)
        if match:
            value = float(match.group(1))
            if 1 <= value <= 100000:
                return value
    return None


def _find_rating(message: str) -> float | None:
    match = re.search(RATING_PATTERN, message)
    if match:
        value = float(match.group(1))
        if 0 <= value <= 5:
            return value
    return None


def _find_attributes(message: str) -> dict[str, str]:
    attributes: dict[str, str] = {}

    for keyword, value in SKIN_TYPES.items():
        if keyword in message:
            attributes["skin_type"] = value
            break

    for keyword, value in SCENTS.items():
        if keyword in message:
            attributes["scent"] = value
            break

    for function in FUNCTIONS:
        if function in message:
            attributes["function"] = function
            break

    if "清爽" in message:
        attributes["texture"] = "清爽"
    elif "滋润" in message:
        attributes["texture"] = "滋润"

    spf_match = re.search(r"spf\s*(\d+)", message, re.IGNORECASE)
    if spf_match:
        attributes["spf"] = spf_match.group(1)

    volume_match = re.search(r"(\d{2,4})\s*(?:ml|毫升)", message, re.IGNORECASE)
    if volume_match:
        attributes["volume_ml"] = volume_match.group(1)

    if "薄荷" in message:
        attributes["flavor"] = "薄荷"
    elif "蜜桃" in message:
        attributes["flavor"] = "蜜桃"
    elif "绿茶" in message:
        attributes["flavor"] = "绿茶"

    return attributes


def _find_priorities(message: str) -> list[str]:
    priorities: list[str] = []
    if any(word in message for word in ("价格优先", "便宜", "性价比", "预算有限")):
        priorities.append("价格")
    if any(word in message for word in ("评分优先", "评分高", "好评")):
        priorities.append("评分")
    if any(word in message for word in ("口碑", "评价多")):
        priorities.append("口碑")
    if any(word in message for word in ("适合", "匹配")):
        priorities.append("偏好")
    return list(dict.fromkeys(priorities))


def _find_exclusions(message: str) -> list[str]:
    keywords: list[str] = []
    for match in re.finditer(EXCLUDE_PATTERN, message):
        value = match.group(1)
        if value in ("这个品牌", "太贵", "贵", "便宜"):
            continue
        keywords.append(value)

    if "不含香精" in message or "无香精" in message:
        keywords.append("香精")

    return list(dict.fromkeys(keywords))


class MockProvider:
    """Deterministic provider for demos, tests, and offline development."""

    name = "mock"

    async def parse_intent(
        self, message: str, profile: ShoppingProfile
    ) -> ShoppingIntent:
        text = message.strip()
        category = _find_category(text)
        budget = _find_budget(text)
        min_rating = _find_rating(text)
        attributes = _find_attributes(text)
        priorities = _find_priorities(text)
        exclusions = _find_exclusions(text)

        brands = [brand for brand in KNOWN_BRANDS if brand in text]

                                                                          
        if budget is None and any(word in text for word in ("便宜", "降价", "低一点")):
            if profile.budget_max:
                budget = round(profile.budget_max * 0.8, 2)

        effective_category = category or profile.category
        needs_clarification = effective_category is None
        question = None
        if needs_clarification:
            question = (
                "What kind of product are you looking for? For example: "
                "body wash, shampoo, face cream, sunscreen, toothpaste, or laundry detergent. "
                "You can also mention a brand, budget, or your top priority."
            )

        return ShoppingIntent(
            category=category,
            query=None,
            budget_max=budget,
            budget_min=None,
            min_rating=min_rating,
            attributes=attributes,
            brands_include=brands,
            brands_exclude=[],
            exclude_keywords=exclusions,
            priorities=priorities,
            needs_clarification=needs_clarification,
            clarification_question=question,
            confidence=0.9 if category else 0.5,
        )

    async def write_recommendation(self, context: RecommendationContext) -> str:
        return self._render(context)

    async def analyze_review(self, content: str, rating: int) -> ReviewAnalysis:
        """Rule-based review analysis for offline demos and LLM fallback."""
        text = content.strip()
        sentences = [
            sentence.strip()
            for sentence in re.split(r"[。！？!?；;，,\n]", text)
            if sentence.strip()
        ]
        pros = [
            sentence[:24]
            for sentence in sentences
            if _has_hint(sentence, POSITIVE_HINTS)
        ][:3]
        cons = [
            sentence[:24]
            for sentence in sentences
            if _has_hint(sentence, NEGATIVE_HINTS)
        ][:3]

        if rating >= 4 and not pros:
            pros = ["good overall experience"]
        if rating <= 2 and not cons:
            cons = ["poor overall experience"]

        tags = list(
            dict.fromkeys(
                label
                for keyword, label in REVIEW_TAG_HINTS.items()
                if keyword in text
            )
        )[:5]
        sentiment = (
            "positive" if rating >= 4 else "negative" if rating <= 2 else "neutral"
        )
        summary = " ".join(text.split())[:60] or "No review text provided."

        return ReviewAnalysis(
            sentiment=sentiment,
            summary=summary,
            pros=pros,
            cons=cons,
            tags=tags,
        )

    async def stream_recommendation(
        self, context: RecommendationContext
    ) -> AsyncIterator[str]:
        text = self._render(context)
        for index in range(0, len(text), 24):
            yield text[index : index + 24]
            await asyncio.sleep(0)

    def _render(self, context: RecommendationContext) -> str:
        scored = context.scored
        if not scored:
            return (
                "I could not find any products that match all of those constraints. "
                "Try relaxing the budget, switching categories, or telling me the two "
                "things you care about most, and I will narrow it down again."
            )

        profile = context.profile
        top = scored[0]
        lines: list[str] = []

        if context.relaxations:
            lines.append("> Note: " + "; ".join(context.relaxations) + ".")
            lines.append("")

        lines.append("### My recommendation")
        lines.append("")
        lines.append("| Rank | Product | Price | Rating | Reviews | Key match |")
        lines.append("|---|---|---|---|---|---|")
        for index, item in enumerate(scored[:3], start=1):
            product = item.product
            match_text = ", ".join(item.reasons[:2]).replace("|", "/")
            lines.append(
                f"| {index} | {product.name} | ¥{product.price:g} | "
                f"{product.rating:.1f} | {product.review_count} | {match_text} |"
            )
        lines.append("")

        lines.append(f"**Top pick: {top.product.name}** ({top.product.brand})")
        lines.append("")
        for reason in top.reasons[:4]:
            lines.append(f"- {reason}")
        if top.warnings:
            lines.append("")
            lines.append("Things to note:")
            for warning in top.warnings[:3]:
                lines.append(f"- {warning}")

        if len(scored) > 1:
            runner_up = scored[1]
            focus = (
                "price"
                if runner_up.product.price < top.product.price
                else "review count"
            )
            lines.append("")
            lines.append(
                f"**Runner-up: {runner_up.product.name}** at "
                f"¥{runner_up.product.price:g}, rated {runner_up.product.rating:.1f}. "
                f"If you care more about {focus}, it is worth comparing."
            )

        lines.append("")
        if profile.budget_max:
            lines.append(
                f"All options above were filtered against your "
                f"¥{profile.budget_max:g} budget. I can narrow the list further by "
                "lower price, higher rating, or a different brand."
            )
        else:
            lines.append(
                "Tell me your budget, skin type, or top priority and I can narrow "
                "the list further."
            )
        return "\n".join(lines)
