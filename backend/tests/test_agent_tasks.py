import pytest

from app.agent.mock import MockProvider
from app.agent.state import AgentPlan, PlanStep
from app.models import Product
from app.services.agent_policy import normalize_plan
from app.services.agent_tasks import create_agent_task, execute_confirmed_task

BUY_GOAL = "帮我找一款适合敏感肌的沐浴露，100 元以内，合适的话我想买两瓶。"
SELL_GOAL = "帮我把这瓶闲置洗发水挂到二手平台，价格定在 60 元。"
FLASH_GOAL = "帮我抢购一瓶沐浴露，预算 100 以内。"


@pytest.mark.asyncio
async def test_mock_planner_builds_buy_plan():
    plan = await MockProvider().plan_tasks(BUY_GOAL)
    assert [step.skill for step in plan.steps] == ["recommend", "order"]
    assert plan.steps[-1].args["quantity"] == 2


@pytest.mark.asyncio
async def test_mock_planner_builds_sell_plan():
    plan = await MockProvider().plan_tasks(SELL_GOAL)
    assert [step.skill for step in plan.steps] == ["sell"]
    assert plan.steps[0].args["category"] == "洗发水"
    assert plan.steps[0].args["price"] == 60


@pytest.mark.asyncio
async def test_mock_planner_builds_flash_sale_plan():
    plan = await MockProvider().plan_tasks(FLASH_GOAL)
    assert [step.skill for step in plan.steps] == ["recommend", "flash_sale"]


def test_policy_forces_confirmation_and_recommend_first():
    plan = AgentPlan(
        goal="buy",
        steps=[PlanStep(skill="order", requires_confirmation=False)],
    )
    normalized = normalize_plan(plan, "buy")
    assert [step.skill for step in normalized.steps] == ["recommend", "order"]
    assert normalized.steps[-1].requires_confirmation is True
    assert normalized.steps[-1].risk == "write"


@pytest.mark.asyncio
async def test_buy_task_stops_for_confirmation_then_orders(db):
    task = await create_agent_task(
        db,
        provider=MockProvider(),
        embedding_provider=None,
        user_id="demo-user",
        goal=BUY_GOAL,
    )
    assert task.status == "awaiting_confirmation"
    assert task.draft is not None
    assert task.draft["skill"] == "order"
    assert task.draft["quantity"] == 2
    assert task.draft["unit_price"] <= 100

    confirmed = execute_confirmed_task(db, task)
    assert confirmed.status == "completed"
    assert any(result.get("skill") == "order" for result in confirmed.results)

    repeated = execute_confirmed_task(db, confirmed)
    assert repeated.status == "completed"
    order_results = [
        result for result in repeated.results if result.get("skill") == "order"
    ]
    assert len(order_results) == 1


@pytest.mark.asyncio
async def test_sell_task_stops_for_confirmation_then_creates_product(db):
    task = await create_agent_task(
        db,
        provider=MockProvider(),
        embedding_provider=None,
        user_id="demo-user",
        goal=SELL_GOAL,
    )
    assert task.status == "awaiting_confirmation"
    assert task.draft is not None
    assert task.draft["skill"] == "sell"
    assert task.draft["category"] == "洗发水"

    confirmed = execute_confirmed_task(db, task)
    assert confirmed.status == "completed"
    sell_result = next(
        result for result in confirmed.results if result.get("skill") == "sell"
    )
    product = db.get(Product, sell_result["product"]["id"])
    assert product is not None
    assert product.seller_id == "demo-user"


@pytest.mark.asyncio
async def test_flash_sale_task_is_high_risk_and_confirmed(db):
    task = await create_agent_task(
        db,
        provider=MockProvider(),
        embedding_provider=None,
        user_id="demo-user",
        goal=FLASH_GOAL,
    )
    assert task.status == "awaiting_confirmation"
    assert task.risk == "high_risk"
    assert task.draft is not None
    assert task.draft["skill"] == "flash_sale"

    confirmed = execute_confirmed_task(db, task)
    assert confirmed.status == "completed"
    assert any(
        result.get("skill") == "flash_sale" for result in confirmed.results
    )
