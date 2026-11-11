import logging

from app.agent.llm import LLMProvider
from app.agent.mock import MockProvider
from app.agent.state import AgentPlan, PlanStep
from app.services.agent_policy import normalize_plan

__all__ = ["AgentPlan", "PlanStep", "plan_goal"]

logger = logging.getLogger(__name__)


async def plan_goal(provider: LLMProvider, goal: str) -> AgentPlan:
    """Plan with the top-level model, then normalize through the policy layer."""
    try:
        plan = await provider.plan_tasks(goal)
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM planning failed, falling back to rules: %s", exc)
        plan = await MockProvider().plan_tasks(goal)
    return normalize_plan(plan, goal)
