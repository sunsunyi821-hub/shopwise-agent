import pytest

from app.agent.mock import MockProvider
from app.agent.state import AgentPlan, PlanStep, ShoppingProfile
from app.agent.supervisor import stream_supervisor_agent
from app.config import Settings
from app.mcp.client import MCPMarketplaceClient
from app.mcp.service import build_marketplace_result
from app.services.agent_policy import normalize_plan

JD_GOAL = "帮我推荐京东上 100 元以内的洗发水，要求评价是可以去除头皮屑，有香气"
COMPARE_GOAL = "帮我找京东和淘宝上 100 元以内的护肤霜，比较价格和评价后推荐三款性价比最高的。"


@pytest.fixture(name="mcp_client")
def mcp_client_fixture():
    # The in-process transport still speaks MCP, without starting a subprocess per test.
    return MCPMarketplaceClient(Settings(mcp_marketplace_inprocess=True))


@pytest.mark.asyncio
async def test_mcp_tools_are_discovered_with_schemas(mcp_client):
    tools = await mcp_client.discover_tools()
    names = {tool["name"] for tool in tools}
    assert names == {
        "search_jd_products",
        "search_taobao_products",
        "get_marketplace_product",
    }
    jd_tool = next(tool for tool in tools if tool["name"] == "search_jd_products")
    assert "query" in jd_tool["input_schema"]["properties"]


@pytest.mark.asyncio
async def test_mcp_search_returns_ranked_products(mcp_client):
    raw = await mcp_client.search(
        query="洗发水 去屑 香气",
        platforms=["jd"],
        category="洗发水",
        budget_max=100,
        limit=3,
    )
    assert raw["platforms"] == ["jd"]
    assert len(raw["payloads"]) == 1
    assert any(call["name"] == "search_jd_products" for call in raw["tool_calls"])

    result = build_marketplace_result(
        query="洗发水 去屑 香气",
        platforms=raw["platforms"],
        payloads=raw["payloads"],
        tool_calls=raw["tool_calls"],
        budget_max=100,
        limit=3,
    )
    assert 1 <= len(result.products) <= 3
    assert all(item.price <= 100 for item in result.products)
    assert all(item.platform == "jd" for item in result.products)
    assert "去屑" in result.products[0].tags or "香气" in result.products[0].tags


@pytest.mark.asyncio
async def test_mock_planner_uses_market_search_for_platform_goals():
    plan = await MockProvider().plan_tasks(COMPARE_GOAL)
    normalized = normalize_plan(plan, COMPARE_GOAL)
    assert [step.skill for step in normalized.steps] == ["market_search"]
    args = normalized.steps[0].args
    assert args["platforms"] == ["jd", "taobao"]
    assert args["category"] == "面霜"
    assert args["budget_max"] == 100
    assert args["limit"] == 3
    assert normalized.steps[0].risk == "read"
    assert normalized.steps[0].requires_confirmation is False


def test_policy_respects_requested_result_count():
    plan = AgentPlan(
        goal=COMPARE_GOAL,
        steps=[
            PlanStep(
                skill="market_search",
                args={"platforms": ["jd", "taobao"], "limit": 5},
            )
        ],
    )
    normalized = normalize_plan(plan, COMPARE_GOAL)
    assert normalized.steps[0].args["limit"] == 3


def test_policy_keeps_external_search_read_only():
    plan = AgentPlan(
        goal=JD_GOAL,
        steps=[
            PlanStep(skill="market_search", args={"platforms": ["jd"]}),
            PlanStep(skill="order", args={"quantity": 1}),
        ],
    )
    normalized = normalize_plan(plan, JD_GOAL)
    assert [step.skill for step in normalized.steps] == ["market_search"]
    assert normalized.steps[0].risk == "read"


@pytest.mark.asyncio
async def test_supervisor_runs_mcp_marketplace_step(db, mcp_client):
    events = [
        event
        async for event in stream_supervisor_agent(
            session=db,
            provider=MockProvider(),
            message=COMPARE_GOAL,
            profile=ShoppingProfile(),
            user_id="demo-user",
            mcp_client=mcp_client,
        )
    ]
    names = [event.event for event in events]
    assert names[0] == "plan"
    assert "marketplace" in names
    assert names[-1] == "_market_final"

    payload = next(
        event.data for event in events if event.event == "marketplace"
    )
    assert payload["platforms"] == ["jd", "taobao"]
    assert 1 <= len(payload["products"]) <= 3
    assert all(item["price"] <= 100 for item in payload["products"])
    assert {item["platform"] for item in payload["products"]} == {"jd", "taobao"}
    assert payload["tool_calls"]
