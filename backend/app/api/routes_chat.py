import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session
from sse_starlette.sse import EventSourceResponse

from app.agent.llm import LLMProvider
from app.agent.orchestrator import (
    AgentResult,
    run_shopping_agent,
)
from app.agent.state import ShoppingProfile
from app.agent.supervisor import stream_supervisor_agent
from app.db import engine, get_session
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ProductOut,
    PurchaseProposal,
    ScoredProductOut,
)
from app.services.sessions import add_message, get_or_create_session, touch_session

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


def _scored_out(item) -> ScoredProductOut:
    return ScoredProductOut(
        product=ProductOut.model_validate(item.product),
        score=item.score,
        breakdown=item.breakdown,
        reasons=item.reasons,
        warnings=item.warnings,
    )








def _proposal_for(result: AgentResult) -> PurchaseProposal | None:
    top_product = result.scored[0].product if result.scored else None
    if top_product is None:
        return None
    return PurchaseProposal(
        product_id=top_product.id,
        product_name=top_product.name,
        quantity=1,
        unit_price=top_product.price,
        total_price=top_product.price,
    )


def _assistant_meta(
    provider: LLMProvider,
    result: AgentResult,
    products_out: list[ScoredProductOut],
    proposal: PurchaseProposal | None,
) -> dict:
    return {
        "provider": getattr(provider, "name", "unknown"),
        "intent": result.intent.model_dump(exclude_none=True),

        "products": [item.model_dump() for item in products_out],
        "product_ids": [item.product.id for item in result.scored],
        "top_product_id": result.top_product_id,
        "purchase_proposal": proposal.model_dump() if proposal else None,
        "clarification": result.clarification,
        "relaxations": result.relaxations,
        "degraded": result.degraded,
    }


def _sse(event: str, data: dict) -> dict[str, str]:
    """sse-starlette formats event/data into SSE frames."""
    return {"event": event, "data": json.dumps(data, ensure_ascii=False)}

@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    request: Request,
    db: Session = Depends(get_session),
) -> ChatResponse:
    chat_session = get_or_create_session(
        db, session_id=payload.session_id, user_id=payload.user_id
    )
    profile = (
        ShoppingProfile.model_validate(chat_session.profile)
        if chat_session.profile
        else ShoppingProfile()
    )

    add_message(db, session_id=chat_session.id, role="user", content=payload.message)

    provider = request.app.state.provider
    embedding_provider = getattr(request.app.state, "embedding_provider", None)
    result = await run_shopping_agent(
        session=db,
        provider=provider,
        message=payload.message,
        profile=profile,
        embedding_provider=embedding_provider,
    )

    products_out = [_scored_out(item) for item in result.scored]
    proposal = _proposal_for(result)

    content = result.clarification or result.recommendation
    add_message(
        db,
        session_id=chat_session.id,
        role="assistant",
        content=content,
        meta=_assistant_meta(provider, result, products_out, proposal),
    )
    touch_session(
        db,
        chat_session,
        profile=result.profile.model_dump(exclude_none=True),
        title=payload.message,
    )

    return ChatResponse(
        session_id=chat_session.id,
        provider=getattr(provider, "name", "unknown"),
        intent=result.intent,
        products=products_out,
        recommendation=result.recommendation,
        top_product_id=result.top_product_id,
        purchase_proposal=proposal,
        clarification=result.clarification,
        degraded=result.degraded,
    )


@router.post("/stream")
async def chat_stream(
    payload: ChatRequest,
    request: Request,
) -> EventSourceResponse:
    """Stream a shopping consultation over SSE.

    The generator owns its Session because the response can stay open for
    tens of seconds; a request-scoped dependency may close too early.
    """
    provider = request.app.state.provider
    embedding_provider = getattr(request.app.state, "embedding_provider", None)
    provider_name = getattr(provider, "name", "unknown")

    async def event_generator() -> AsyncIterator[dict[str, str]]:
        with Session(engine) as db:
            try:
                chat_session = get_or_create_session(
                    db, session_id=payload.session_id, user_id=payload.user_id
                )
                profile = (
                    ShoppingProfile.model_validate(chat_session.profile)
                    if chat_session.profile
                    else ShoppingProfile()
                )
                add_message(
                    db,
                    session_id=chat_session.id,
                    role="user",
                    content=payload.message,
                )


                yield _sse(
                    "session",
                    {"session_id": chat_session.id, "provider": provider_name},
                )

                result: AgentResult | None = None
                task_data: dict | None = None
                market_data: dict | None = None
                async for event in stream_supervisor_agent(
                    session=db,
                    provider=provider,
                    message=payload.message,
                    profile=profile,
                    user_id=payload.user_id,
                    embedding_provider=embedding_provider,
                    mcp_client=getattr(request.app.state, "mcp", None),
                ):
                    if event.event == "_final":
                        result = event.data["result"]
                        continue

                    if event.event == "_market_final":
                        market_data = event.data["result"]
                        continue

                    if event.event == "task":
                        task_data = event.data["task"]

                    if event.event == "marketplace":
                        market_data = event.data
                        yield _sse(
                            "marketplace",
                            {**event.data, "provider": provider_name},
                        )
                        continue

                    if event.event == "products":
                        yield _sse(
                            "products",
                            {
                                "products": [
                                    _scored_out(item).model_dump()
                                    for item in event.data["products"]
                                ],
                                "relaxations": event.data.get("relaxations", []),
                            },
                        )
                        continue

                    yield _sse(event.event, event.data)

                if task_data is not None:
                    summary = (
                        (task_data.get("plan") or {}).get("summary")
                        or "The task is ready and waiting for your confirmation."
                    )
                    recommend_result = next(
                        (
                            item
                            for item in task_data.get("results", [])
                            if item.get("skill") == "recommend"
                        ),
                        None,
                    )
                    meta = {
                        "provider": provider_name,
                        "task_id": task_data.get("id"),
                        "task": task_data,
                        "status": task_data.get("status"),
                    }
                    if recommend_result:
                        meta.update(
                            {
                                "products": recommend_result.get("products", []),
                                "top_product_id": recommend_result.get(
                                    "top_product_id"
                                ),
                                "recommendation": recommend_result.get(
                                    "summary", ""
                                ),
                                "relaxations": recommend_result.get(
                                    "relaxations", []
                                ),
                            }
                        )
                    assistant_message = add_message(
                        db,
                        session_id=chat_session.id,
                        role="assistant",
                        content=summary,
                        meta=meta,
                    )
                    touch_session(
                        db,
                        chat_session,
                        profile=profile.model_dump(exclude_none=True),
                        title=payload.message,
                    )
                    yield _sse(
                        "done",
                        {
                            "session_id": chat_session.id,
                            "message_id": assistant_message.id,
                        },
                    )
                    return

                if market_data is not None:
                    assistant_message = add_message(
                        db,
                        session_id=chat_session.id,
                        role="assistant",
                        content=str(market_data.get("recommendation", "")),
                        meta={
                            "provider": provider_name,
                            "marketplace": market_data,
                            "mcp": {
                                "tool_calls": market_data.get("tool_calls", []),
                                "platforms": market_data.get("platforms", []),
                            },
                        },
                    )
                    touch_session(
                        db,
                        chat_session,
                        profile=profile.model_dump(exclude_none=True),
                        title=payload.message,
                    )
                    yield _sse(
                        "done",
                        {
                            "session_id": chat_session.id,
                            "message_id": assistant_message.id,
                        },
                    )
                    return

                if result is None:
                    raise RuntimeError("Agent stream finished without a result")

                products_out = [_scored_out(item) for item in result.scored]
                proposal = _proposal_for(result)
                assistant_message = add_message(
                    db,
                    session_id=chat_session.id,
                    role="assistant",
                    content=result.clarification or result.recommendation,
                    meta=_assistant_meta(provider, result, products_out, proposal),
                )
                touch_session(
                    db,
                    chat_session,
                    profile=result.profile.model_dump(exclude_none=True),
                    title=payload.message,
                )


                yield _sse(
                    "recommendation",
                    {
                        "provider": provider_name,
                        "recommendation": result.recommendation,
                        "top_product_id": result.top_product_id,
                        "purchase_proposal": (
                            proposal.model_dump() if proposal else None
                        ),
                        "clarification": result.clarification,
                        "relaxations": result.relaxations,
                        "degraded": result.degraded,
                    },
                )
                yield _sse(
                    "done",
                    {
                        "session_id": chat_session.id,
                        "message_id": assistant_message.id,
                    },
                )
            except HTTPException as exc:
                yield _sse(
                    "error",
                    {"code": exc.status_code, "message": exc.detail},
                )
            except Exception:
                logger.exception("Streaming chat failed")
                yield _sse(
                    "error",
                    {"message": "Streaming request failed. Please try again."},
                )

    return EventSourceResponse(event_generator(), ping=15)
