import logging
from collections.abc import AsyncIterator
from typing import TypedDict
from uuid import uuid4

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from sqlmodel import Session

from app.agent.embeddings import EmbeddingProvider
from app.agent.llm import LLMProvider
from app.agent.orchestrator import AgentEvent, AgentResult
from app.agent.planning import AgentPlan, plan_goal
from app.agent.state import ScoredProduct, ShoppingProfile
from app.agent.tools import build_agent_tools
from app.mcp.client import MCPMarketplaceClient
from app.models import AgentTask
from app.schemas import AgentTaskOut, ProductOut, ScoredProductOut
from app.services.agent_policy import PlanValidationError
from app.workflows.recommendation import stream_recommendation_workflow

logger = logging.getLogger(__name__)


class SupervisorState(TypedDict, total=False):
    goal: str
    profile: ShoppingProfile
    plan: dict
    index: int
    results: list[dict]
    status: str
    task_id: str | None
    top_product: ScoredProduct
    final_result: AgentResult
    market_result: dict


class SupervisorConfig(TypedDict, total=False):
    session: Session
    provider: LLMProvider
    embedding_provider: EmbeddingProvider | None
    user_id: str
    mcp_client: MCPMarketplaceClient | None
    tools: dict[str, BaseTool]


def _emit(event: AgentEvent) -> None:
    get_stream_writer()(event)


def _scored_payload(item: ScoredProduct) -> dict:
    return ScoredProductOut(
        product=ProductOut.model_validate(item.product),
        score=item.score,
        breakdown=item.breakdown,
        reasons=item.reasons,
        warnings=item.warnings,
    ).model_dump(mode="json")


def _task_payload(task: AgentTask) -> dict:
    return AgentTaskOut.model_validate(task).model_dump(mode="json")


def _create_task(
    db: Session,
    *,
    user_id: str,
    goal: str,
    plan: AgentPlan,
    results: list[dict],
    draft: dict,
    risk: str,
) -> AgentTask:
    task = AgentTask(
        id=uuid4().hex,
        user_id=user_id,
        goal=goal,
        status="awaiting_confirmation",
        risk=risk,
        plan=plan.model_dump(),
        results=results,
        draft=draft,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


async def plan_node(
    state: SupervisorState,
    config: RunnableConfig,
) -> dict:
    provider: LLMProvider = config["configurable"]["provider"]
    try:
        plan = await plan_goal(provider, state["goal"])
    except PlanValidationError as exc:
        _emit(AgentEvent("error", {"message": str(exc)}))
        return {"status": "failed", "results": []}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Supervisor planning failed: %s", exc)
        _emit(AgentEvent("error", {"message": "Task planning failed"}))
        return {"status": "failed", "results": []}

    _emit(AgentEvent("plan", {"plan": plan.model_dump()}))
    return {
        "plan": plan.model_dump(),
        "index": 0,
        "results": [],
        "status": "running",
    }


async def execute_node(
    state: SupervisorState,
    config: RunnableConfig,
) -> dict:
    plan = AgentPlan.model_validate(state["plan"])
    index = int(state.get("index", 0))
    step = plan.steps[index]
    results = list(state.get("results", []))
    profile = state.get("profile") or ShoppingProfile()
    db: Session = config["configurable"]["session"]
    provider: LLMProvider = config["configurable"]["provider"]
    embedding_provider = config["configurable"].get("embedding_provider")
    user_id: str = config["configurable"]["user_id"]
    tools: dict[str, BaseTool] = config["configurable"]["tools"]
    next_index = index + 1

    if step.skill == "market_search":
        tool = tools.get("search_external_marketplace")
        if tool is None:
            _emit(AgentEvent("error", {"message": "MCP marketplace search is unavailable"}))
            return {"status": "failed", "index": next_index, "results": results}

        platforms = step.args.get("platforms") or ["jd", "taobao"]
        try:
            payload = await tool.ainvoke(
                {
                    "query": str(step.args.get("query") or state["goal"]),
                    "platforms": platforms,
                    "category": step.args.get("category"),
                    "budget_max": step.args.get("budget_max"),
                    "limit": int(step.args.get("limit") or 3),
                }
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("MCP marketplace workflow failed: %s", exc)
            _emit(AgentEvent("error", {"message": f"External marketplace search failed: {exc}"}))
            return {"status": "failed", "index": next_index, "results": results}

        products = payload.get("products", [])
        summary = (
            f"Searched {len(payload.get('platforms', []))} platform(s) through MCP; "
            f"recommended {len(products)} product(s) after comparing price and reviews"
        )
        results = [
            *results,
            {
                "skill": "market_search",
                "summary": summary,
                "platforms": payload.get("platforms", []),
                "products": products,
                "tool_calls": payload.get("tool_calls", []),
            },
        ]
        _emit(AgentEvent("marketplace", payload))
        _emit(AgentEvent("_market_final", {"result": payload}))
        return {
            "status": "completed",
            "index": next_index,
            "results": results,
            "market_result": payload,
        }

    if step.skill == "recommend":
        result: AgentResult | None = None
        async for event in stream_recommendation_workflow(
            session=db,
            provider=provider,
            message=state["goal"],
            profile=profile,
            embedding_provider=embedding_provider,
        ):
            if event.event == "_final":
                result = event.data["result"]
            else:
                _emit(event)

        if result is None:
            _emit(AgentEvent("error", {"message": "Recommendation workflow returned no result"}))
            return {"status": "failed", "index": next_index, "results": results}

        if result.scored:
            top = result.scored[0].product
            summary = (
                f"Found {len(result.scored)} candidates; "
                f"top pick: {top.name} (¥{top.price:g})"
            )
        else:
            summary = result.clarification or "No matching products"

        results = [
            *results,
            {
                "skill": "recommend",
                "summary": summary,
                "top_product_id": result.top_product_id,
                "products": [_scored_payload(item) for item in result.scored],
                "relaxations": result.relaxations,
            },
        ]
        top_product = result.scored[0] if result.scored else None
        status = (
            "needs_input"
            if result.clarification or not result.scored
            else "running"
        )

        if status == "needs_input":
            _emit(AgentEvent("_final", {"result": result}))
            return {
                "results": results,
                "index": next_index,
                "status": status,
                "final_result": result,
            }

        if next_index >= len(plan.steps):
            _emit(AgentEvent("_final", {"result": result}))

        return {
            "results": results,
            "index": next_index,
            "status": status,
            "top_product": top_product,
            "final_result": result,
        }

    if step.skill == "order":
        top_product = state.get("top_product")
        if top_product is None:
            _emit(AgentEvent("error", {"message": "No product available to order"}))
            return {"status": "failed", "index": next_index, "results": results}
        tool_result = await tools["prepare_order"].ainvoke(
            {
                "product_id": top_product.product.id,
                "quantity": int(step.args.get("quantity") or 1),
            }
        )
        if tool_result.get("error"):
            _emit(AgentEvent("error", {"message": tool_result["error"]}))
            return {"status": "failed", "index": next_index, "results": results}
        draft = tool_result["draft"]
        max_price = step.args.get("max_price")
        if max_price is not None and draft["unit_price"] > float(max_price):
            _emit(AgentEvent("error", {"message": "Recommended product exceeds the accepted price"}))
            return {"status": "failed", "index": next_index, "results": results}
        task = _create_task(
            db,
            user_id=user_id,
            goal=state["goal"],
            plan=plan,
            results=results,
            draft=draft,
            risk=step.risk,
        )
        _emit(AgentEvent("task", {"task": _task_payload(task)}))
        return {
            "status": "awaiting_confirmation",
            "task_id": task.id,
            "results": results,
            "index": next_index,
        }

    if step.skill == "sell":
        from app.services.agent_tasks import _enrich_sell_args
        from app.services.catalog import list_categories

        valid_categories = set(list_categories(db))
        sell_args = await _enrich_sell_args(
            state["goal"], step.args, valid_categories
        )
        category = str(sell_args.get("category") or "")
        price = sell_args.get("price")
        if not category or category not in valid_categories:
            _emit(AgentEvent("error", {"message": "Please specify a product category"}))
            return {"status": "failed", "index": next_index, "results": results}
        if price is None:
            _emit(AgentEvent("error", {"message": "Please specify a product price"}))
            return {"status": "failed", "index": next_index, "results": results}

        tool_result = await tools["prepare_selling"].ainvoke(
            {
                "description": str(sell_args.get("description") or state["goal"]),
                "category": category,
                "price": float(price),
                "brand": sell_args.get("brand"),
            }
        )
        if tool_result.get("error"):
            _emit(AgentEvent("error", {"message": tool_result["error"]}))
            return {"status": "failed", "index": next_index, "results": results}
        task = _create_task(
            db,
            user_id=user_id,
            goal=state["goal"],
            plan=plan,
            results=results,
            draft=tool_result["draft"],
            risk=step.risk,
        )
        _emit(AgentEvent("task", {"task": _task_payload(task)}))
        return {
            "status": "awaiting_confirmation",
            "task_id": task.id,
            "results": results,
            "index": next_index,
        }

    if step.skill == "flash_sale":
        top_product = state.get("top_product")
        if top_product is None:
            _emit(AgentEvent("error", {"message": "No product available for flash purchase"}))
            return {"status": "failed", "index": next_index, "results": results}
        tool_result = await tools["prepare_flash_sale"].ainvoke(
            {
                "product_id": top_product.product.id,
                "quantity": int(step.args.get("quantity") or 1),
                "max_price": step.args.get("max_price"),
            }
        )
        if tool_result.get("error"):
            _emit(AgentEvent("error", {"message": tool_result["error"]}))
            return {"status": "failed", "index": next_index, "results": results}
        task = _create_task(
            db,
            user_id=user_id,
            goal=state["goal"],
            plan=plan,
            results=results,
            draft=tool_result["draft"],
            risk=step.risk,
        )
        _emit(AgentEvent("task", {"task": _task_payload(task)}))
        return {
            "status": "awaiting_confirmation",
            "task_id": task.id,
            "results": results,
            "index": next_index,
        }

    _emit(AgentEvent("error", {"message": "Unknown skill"}))
    return {"status": "failed", "index": next_index, "results": results}


def route_after_execute(state: SupervisorState) -> str:
    if state.get("status") in {"awaiting_confirmation", "failed", "needs_input"}:
        return "end"
    plan = AgentPlan.model_validate(state["plan"])
    if int(state.get("index", 0)) >= len(plan.steps):
        return "end"
    return "execute"


def build_supervisor_graph():
    graph = StateGraph(SupervisorState)
    graph.add_node("plan", plan_node)
    graph.add_node("execute", execute_node)
    graph.add_edge(START, "plan")
    graph.add_edge("plan", "execute")
    graph.add_conditional_edges(
        "execute",
        route_after_execute,
        {"execute": "execute", "end": END},
    )
    return graph.compile()


supervisor_graph = build_supervisor_graph()


async def stream_supervisor_agent(
    *,
    session: Session,
    provider: LLMProvider,
    message: str,
    profile: ShoppingProfile,
    user_id: str,
    embedding_provider: EmbeddingProvider | None = None,
    mcp_client: MCPMarketplaceClient | None = None,
) -> AsyncIterator[AgentEvent]:
    """Chat entrypoint: the supervisor plans and invokes workflow tools."""
    tools = build_agent_tools(
        db=session,
        provider=provider,
        embedding_provider=embedding_provider,
        user_id=user_id,
        mcp_client=mcp_client,
    )
    config: RunnableConfig = {
        "configurable": {
            "session": session,
            "provider": provider,
            "embedding_provider": embedding_provider,
            "user_id": user_id,
            "mcp_client": mcp_client,
            "tools": tools,
        }
    }
    async for event in supervisor_graph.astream(
        {"goal": message, "profile": profile},
        config=config,
        stream_mode="custom",
    ):
        if isinstance(event, AgentEvent):
            yield event
