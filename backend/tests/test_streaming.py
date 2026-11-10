import pytest

from app.agent.mock import MockProvider
from app.agent.orchestrator import stream_shopping_agent
from app.agent.state import ShoppingProfile


@pytest.mark.asyncio
async def test_stream_agent_emits_stages_products_and_tokens(db):
    events = [
        event
        async for event in stream_shopping_agent(
            session=db,
            provider=MockProvider(),
            message="我想买一瓶沐浴露，预算 100 以内，敏感肌，最好没有香味",
            profile=ShoppingProfile(),
        )
    ]

    names = [event.event for event in events]
    assert names[0] == "stage"
    assert events[0].data["stage"] == "parse_intent"
    assert "intent" in names
    assert "products" in names
    assert "token" in names
    assert names[-1] == "_final"

    result = events[-1].data["result"]
    assert result.scored
    assert result.recommendation
    assert result.top_product_id
    assert result.profile.category == "沐浴露"


@pytest.mark.asyncio
async def test_stream_agent_clarification_skips_product_events(db):
    events = [
        event
        async for event in stream_shopping_agent(
            session=db,
            provider=MockProvider(),
            message="你好，帮我看看买点什么好",
            profile=ShoppingProfile(),
        )
    ]

    names = [event.event for event in events]
    assert "products" not in names
    result = events[-1].data["result"]
    assert result.clarification is not None
