import pytest

from app.agent.mock import MockProvider
from app.agent.orchestrator import run_shopping_agent
from app.agent.state import ShoppingProfile


@pytest.mark.asyncio
async def test_agent_understands_budget_and_preferences(db):
    provider = MockProvider()
    result = await run_shopping_agent(
        session=db,
        provider=provider,
        message="我想买一瓶沐浴露，预算100以内，敏感肌，最好没有香味",
        profile=ShoppingProfile(),
    )

    assert result.intent.category == "沐浴露"
    assert result.intent.budget_max == 100
    assert result.intent.attributes["skin_type"] == "敏感肌"
    assert result.intent.attributes["scent"] == "无香"
    assert result.scored
    assert result.top_product_id is not None
    assert all(item.product.price <= 100 for item in result.scored)

    top = result.scored[0].product
    assert top.attributes["skin_type"] == "敏感肌"
    assert top.attributes["scent"] == "无香"
    assert "Top pick:" in result.recommendation


@pytest.mark.asyncio
async def test_agent_asks_for_category_when_missing(db):
    result = await run_shopping_agent(
        session=db,
        provider=MockProvider(),
        message="你好，帮我看看买点什么好",
        profile=ShoppingProfile(),
    )
    assert result.clarification is not None
    assert "What kind of product" in result.clarification
    assert result.scored == []


@pytest.mark.asyncio
async def test_agent_relaxes_budget_when_no_match(db):
    result = await run_shopping_agent(
        session=db,
        provider=MockProvider(),
        message="沐浴露，预算10元以内",
        profile=ShoppingProfile(),
    )
    assert result.relaxations
    assert result.scored


@pytest.mark.asyncio
async def test_agent_reports_when_nothing_matches(db):
    result = await run_shopping_agent(
        session=db,
        provider=MockProvider(),
        message="预算 100 以内",
        profile=ShoppingProfile(
            category="沐浴露",
            brands_include=["不存在的品牌"],
        ),
    )
    assert result.scored == []
    assert "No products" in result.recommendation
