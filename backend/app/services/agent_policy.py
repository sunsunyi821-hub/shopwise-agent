import logging
from typing import Any

from app.agent.state import AgentPlan, PlanStep

logger = logging.getLogger(__name__)

ALLOWED_SKILLS = {"recommend", "order", "sell", "flash_sale"}
SKILL_RISK = {
    "recommend": "read",
    "order": "write",
    "sell": "write",
    "flash_sale": "high_risk",
}
MAX_STEPS = 4
MAX_QUANTITY = 5
MAX_TOTAL = 5000.0


class PlanValidationError(ValueError):
    pass


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def normalize_plan(plan: AgentPlan, goal: str) -> AgentPlan:
    """Validate and normalize a plan; policy owns risk and confirmation."""
    if not plan.steps:
        plan.steps = [PlanStep(skill="recommend")]

    if len(plan.steps) > MAX_STEPS:
        raise PlanValidationError(f"A plan may contain at most {MAX_STEPS} steps")

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
