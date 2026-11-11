import logging
import re
from typing import Any

from app.agent.state import AgentPlan, PlanStep

logger = logging.getLogger(__name__)

ALLOWED_SKILLS = {"recommend", "market_search", "order", "sell", "flash_sale"}
SKILL_RISK = {
    "recommend": "read",
    "market_search": "read",
    "order": "write",
    "sell": "write",
    "flash_sale": "high_risk",
}
MAX_STEPS = 4
MAX_QUANTITY = 5
MAX_TOTAL = 5000.0
MAX_MARKET_RESULTS = 5

PLATFORM_ALIASES = {
    "京东": "jd",
    "jd": "jd",
    "淘宝": "taobao",
    "天猫": "taobao",
    "taobao": "taobao",
}
MARKET_CATEGORY_ALIASES = {
    "护肤霜": "面霜",
    "护肤": "面霜",
}
RESULT_COUNT_WORDS = {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5}


def _requested_result_limit(goal: str) -> int | None:
    match = re.search(r"(\d+|[一两二三四五])\s*款", goal)
    if not match:
        return None
    value = match.group(1)
    limit = int(value) if value.isdigit() else RESULT_COUNT_WORDS.get(value)
    return max(1, min(MAX_MARKET_RESULTS, limit)) if limit else None


class PlanValidationError(ValueError):
    pass


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _platforms_from_goal(goal: str) -> list[str]:
    text = goal.lower()
    platforms: list[str] = []
    if "jd" in text or "京东" in text:
        platforms.append("jd")
    if "taobao" in text or "淘宝" in text or "天猫" in text:
        platforms.append("taobao")
    return platforms


def _normalize_market_args(goal: str, args: dict[str, Any]) -> dict[str, Any]:
    """External search is read-only; cap platforms, results, and budget."""
    platforms = args.get("platforms")
    if isinstance(platforms, str):
        platforms = [platforms]
    normalized_platforms = [
        PLATFORM_ALIASES[str(item).strip().lower()]
        for item in (platforms or _platforms_from_goal(goal))
        if str(item).strip().lower() in PLATFORM_ALIASES
    ]
    if not normalized_platforms:
        normalized_platforms = _platforms_from_goal(goal) or ["jd", "taobao"]

    category = str(args.get("category") or "").strip()
    category = MARKET_CATEGORY_ALIASES.get(category, category) or None

    budget = _number(args.get("budget_max"))
    if budget is not None and budget > MAX_TOTAL:
        raise PlanValidationError("Marketplace search budget exceeds the system limit")

    try:
        limit = int(args.get("limit") or 3)
    except (TypeError, ValueError):
        limit = 3
    limit = max(1, min(MAX_MARKET_RESULTS, limit))
    requested_limit = _requested_result_limit(goal)
    if requested_limit is not None:
        limit = requested_limit

    return {
        **args,
        "platforms": list(dict.fromkeys(normalized_platforms)),
        "query": str(args.get("query") or goal)[:500],
        "category": category,
        "budget_max": budget,
        "limit": limit,
    }


def normalize_plan(plan: AgentPlan, goal: str) -> AgentPlan:
    """Validate and normalize a plan; policy owns risk and confirmation."""
    if not plan.steps:
        plan.steps = [PlanStep(skill="recommend")]

    if len(plan.steps) > MAX_STEPS:
        raise PlanValidationError(f"A plan may contain at most {MAX_STEPS} steps")

    market_step = next(
        (step for step in plan.steps if step.skill == "market_search"), None
    )
    if market_step is not None:
        return AgentPlan(
            goal=goal or plan.goal,
            summary=plan.summary
            or "Search external marketplaces through MCP and compare price and reviews",
            steps=[
                PlanStep(
                    skill="market_search",
                    args=_normalize_market_args(goal, dict(market_step.args)),
                    risk="read",
                    requires_confirmation=False,
                )
            ],
        )

    steps: list[PlanStep] = []
    seen_recommend = False

    for step in plan.steps:
        skill = step.skill
        if skill not in ALLOWED_SKILLS:
            raise PlanValidationError(f"Unsupported skill: {skill}")

        if skill in {"order", "flash_sale"} and not seen_recommend:
            steps.append(PlanStep(skill="recommend", args={}))
            seen_recommend = True

        args = dict(step.args)
        quantity = int(args.get("quantity") or 1)
        quantity = max(1, min(MAX_QUANTITY, quantity))
        args["quantity"] = quantity

        if skill in {"order", "flash_sale"}:
            max_price = _number(args.get("max_price"))
            if max_price is not None:
                if max_price > MAX_TOTAL:
                    raise PlanValidationError("Unit price exceeds the system limit")
                args["max_price"] = max_price
                if max_price * quantity > MAX_TOTAL:
                    raise PlanValidationError("Order total exceeds the system limit")
            else:
                args["max_price"] = None

        if skill == "sell":
            price = _number(args.get("price"))
            if price is not None and price > MAX_TOTAL:
                raise PlanValidationError("Listing price exceeds the system limit")
            args["price"] = price

        risk = SKILL_RISK[skill]
        steps.append(
            PlanStep(
                skill=skill,
                args=args,
                risk=risk,
                requires_confirmation=risk != "read",
            )
        )
        if skill == "recommend":
            seen_recommend = True

    risk = "read"
    if any(step.risk == "high_risk" for step in steps):
        risk = "high_risk"
    elif any(step.risk == "write" for step in steps):
        risk = "write"

    return AgentPlan(
        goal=goal or plan.goal,
        summary=plan.summary or "Execute the plan",
        steps=steps,
    )
