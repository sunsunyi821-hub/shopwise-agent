import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, TypedDict, cast

from langchain_core.runnables import RunnableConfig
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from sqlmodel import Session

from app.agent.embeddings import EmbeddingProvider
from app.agent.llm import LLMProvider
from app.agent.mock import MockProvider
from app.agent.state import (
    RecommendationContext,
    ScoredProduct,
    ShoppingIntent,
    ShoppingProfile,
)
from app.models import Product
from app.services.catalog import search_for_profile
from app.services.ranking import rank_products
from app.services.semantic import build_query_text, compute_semantic_scores

logger = logging.getLogger(__name__)
                                    
                                


@dataclass
class AgentResult:
    """Final result returned by the shopping agent."""

    intent: ShoppingIntent
    profile: ShoppingProfile
    scored: list[ScoredProduct] = field(default_factory=list)                
                                 
                                      
    recommendation: str = ""
    top_product_id: str | None = None
    clarification: str | None = None
    relaxations: list[str] = field(default_factory=list)
    degraded: bool = False


@dataclass
class AgentEvent:
    """One event emitted by the streaming agent."""

    event: str
    data: dict[str, Any] = field(default_factory=dict)

                         
      
      
      
       
          
                    

        
        
                  
 
          
        
                      
 
       
           
      
 
        
             
               
@dataclass
class IntentPreparation:
    """Intent plus the merged profile and degradation flag."""

    intent: ShoppingIntent
    profile: ShoppingProfile
    degraded: bool


                                                                             
                   
 
                                         
                                          
 
                                           
                                    
 
                                                    
                                                                             
class ShoppingGraphState(TypedDict, total=False):
    message: str
    profile: ShoppingProfile
    intent: ShoppingIntent
    degraded: bool
    clarification: str | None
    products: list[Product]
    relaxations: list[str]
    scored: list[ScoredProduct]
    recommendation: str
    top_product_id: str | None


class ShoppingGraphConfig(TypedDict, total=False):
    """Runtime dependencies live in config rather than graph state.

    State holds data that changes as the workflow runs; database sessions and
    model clients are dependencies and belong in config["configurable"].
    """

    session: Session
    provider: LLMProvider
    embedding_provider: EmbeddingProvider | None
    stream_recommendation: bool


STAGE_LABELS = {
    "parse_intent": "Understand request",
    "search": "Search products",
    "analyze": "Analyze reviews",
    "rank": "Rank products",
    "recommend": "Write recommendation",
}


def _stage(stage: str, status: str) -> AgentEvent:
    """status is either active or done; the UI uses it to animate the trace."""
    return AgentEvent(
        "stage",
        {"stage": stage, "status": status, "label": STAGE_LABELS[stage]},
    )


def _emit(event: AgentEvent) -> None:
    """Emit a custom event from inside a node.

    get_stream_writer() delivers events during graph.astream(...,
    stream_mode="custom"); during graph.ainvoke(...) it is a no-op, so the
    same nodes serve both streaming and non-streaming entry points.
    """
    get_stream_writer()(event)


def _result_from_state(
    state: ShoppingGraphState, **overrides: Any
) -> AgentResult:
    """Convert graph state into AgentResult for the API layer."""
    values: dict[str, Any] = {
        "intent": state["intent"],
        "profile": state["profile"],
        "scored": state.get("scored", []),
        "recommendation": state.get("recommendation", ""),
        "top_product_id": state.get("top_product_id"),
        "clarification": state.get("clarification"),
        "relaxations": state.get("relaxations", []),
        "degraded": state.get("degraded", False),
    }
    values.update(overrides)
    return AgentResult(**values)


async def _prepare_intent(
    provider: LLMProvider,
    message: str,
    profile: ShoppingProfile,
) -> IntentPreparation:
                                     
    try:
        intent = await provider.parse_intent(message, profile)
        degraded = False
    except Exception as exc:                                                               
        logger.warning(
            "Intent parsing failed (%s), falling back to rules: %s",
            provider.name,
            exc,
        )
        intent = await MockProvider().parse_intent(message, profile)
        degraded = True

                                                  
    return IntentPreparation(
        intent=intent,
        profile=profile.merged_with(intent),
        degraded=degraded,
    )


def _clarification_for(
    intent: ShoppingIntent,
    profile: ShoppingProfile,
) -> str | None:
    if intent.needs_clarification or not profile.category:
                              
        return (
            intent.clarification_question
            or "What kind of product are you looking for? For example: body wash, shampoo, or face cream."
        )
    return None


async def _score_candidates(
    *,
    session: Session,
    message: str,
    profile: ShoppingProfile,
    products: list[Product],
    embedding_provider: EmbeddingProvider | None,
) -> list[ScoredProduct]:
    semantic_scores: dict[str, float] = {}
                                               
    if embedding_provider is not None:
        query_text = build_query_text(message, profile)
        try:
            semantic_scores = await compute_semantic_scores(
                session, embedding_provider, query_text
            )
        except Exception as exc:                                                         
                                                       
            logger.warning(
                "Semantic scoring failed (%s), continuing without it: %s",
                getattr(embedding_provider, "model", "unknown"),
                exc,
            )

    return rank_products(products, profile, semantic_scores=semantic_scores)[:5]


def _recommendation_context(
    *,
    profile: ShoppingProfile,
    intent: ShoppingIntent,
    scored: list[ScoredProduct],
    relaxations: list[str],
) -> RecommendationContext:
    return RecommendationContext(
        profile=profile,
        intent=intent,
        scored=scored,
        relaxations=relaxations,
    )


async def _write_recommendation(
    provider: LLMProvider,
    context: RecommendationContext,
) -> tuple[str, bool]:
    try:
        return await provider.write_recommendation(context), False
    except Exception as exc:                
        logger.warning(
            "Recommendation generation failed (%s), falling back to template: %s",
            provider.name,
            exc,
        )
        return await MockProvider().write_recommendation(context), True


                                                                             
      
 
                                
                                  
                                                                             
async def parse_intent_node(
    state: ShoppingGraphState,
    config: RunnableConfig,
) -> dict:
    _emit(_stage("parse_intent", "active"))
    provider: LLMProvider = config["configurable"]["provider"]
    prepared = await _prepare_intent(provider, state["message"], state["profile"])

    _emit(
        AgentEvent(
            "intent",
            {"intent": prepared.intent.model_dump(exclude_none=True)},
        )
    )
    _emit(_stage("parse_intent", "done"))

    return {
        "intent": prepared.intent,
        "profile": prepared.profile,
        "degraded": prepared.degraded,
        "clarification": _clarification_for(prepared.intent, prepared.profile),
    }


def route_after_intent(state: ShoppingGraphState) -> str:
    """Conditional edge: clarify when needed, otherwise search."""
    return "clarify" if state.get("clarification") else "search"


async def clarify_node(state: ShoppingGraphState) -> dict:
                                      
    _emit(AgentEvent("_final", {"result": _result_from_state(state)}))
    return {}


async def search_node(
    state: ShoppingGraphState,
    config: RunnableConfig,
) -> dict:
    _emit(_stage("search", "active"))
    session: Session = config["configurable"]["session"]
    search = search_for_profile(session, state["profile"])
    _emit(_stage("search", "done"))

    return {
        "products": search.products,
        "relaxations": search.relaxations,
    }


def route_after_search(state: ShoppingGraphState) -> str:
    """Conditional edge: no_results when empty, otherwise analyze."""
    return "no_results" if not state.get("products") else "analyze"


async def no_results_node(state: ShoppingGraphState) -> dict:
    recommendation = (
        "No products in the catalog match all of those constraints. "
        "Try relaxing the budget, switching categories, or removing one hard constraint."
    )
    _emit(
        AgentEvent(
            "_final",
            {"result": _result_from_state(state, recommendation=recommendation)},
        )
    )
    return {"recommendation": recommendation}


async def analyze_node(state: ShoppingGraphState) -> dict:
                                   
                               
    _emit(_stage("analyze", "active"))
    _emit(_stage("analyze", "done"))
    return {}


async def rank_node(
    state: ShoppingGraphState,
    config: RunnableConfig,
) -> dict:
    _emit(_stage("rank", "active"))
    scored = await _score_candidates(
        session=config["configurable"]["session"],
        message=state["message"],
        profile=state["profile"],
        products=state.get("products", []),
        embedding_provider=config["configurable"].get("embedding_provider"),
    )
    _emit(
        AgentEvent(
            "products",
            {
                "products": scored,
                "relaxations": state.get("relaxations", []),
            },
        )
    )
    _emit(_stage("rank", "done"))
    return {"scored": scored}


async def recommend_node(
    state: ShoppingGraphState,
    config: RunnableConfig,
) -> dict:
    provider: LLMProvider = config["configurable"]["provider"]
    scored = state.get("scored", [])
    context = _recommendation_context(
        profile=state["profile"],
        intent=state["intent"],
        scored=scored,
        relaxations=state.get("relaxations", []),
    )

    _emit(_stage("recommend", "active"))
    degraded = state.get("degraded", False)
    recommendation = ""

    if config["configurable"].get("stream_recommendation"):
                             
        chunks: list[str] = []
        try:
            async for token in provider.stream_recommendation(context):
                chunks.append(token)
                _emit(AgentEvent("token", {"text": token}))
            recommendation = "".join(chunks)
        except Exception as exc:                
            logger.warning(
                "Streaming recommendation failed (%s), falling back to template: %s",
                provider.name,
                exc,
            )
            recommendation = await MockProvider().write_recommendation(context)
            degraded = True
    else:
                         
        recommendation, recommendation_degraded = await _write_recommendation(
            provider, context
        )
        degraded = degraded or recommendation_degraded

                                 
    if not recommendation.strip():
        recommendation = await MockProvider().write_recommendation(context)
        degraded = True

    top_product_id = scored[0].product.id if scored else None
    _emit(_stage("recommend", "done"))
    _emit(
        AgentEvent(
            "_final",
            {
                "result": _result_from_state(
                    state,
                    recommendation=recommendation,
                    top_product_id=top_product_id,
                    degraded=degraded,
                )
            },
        )
    )

    return {
        "recommendation": recommendation,
        "top_product_id": top_product_id,
        "degraded": degraded,
    }


def build_shopping_graph():
    """Assemble nodes and edges, then compile the graph."""
    graph = StateGraph(ShoppingGraphState)

    graph.add_node("parse_intent", parse_intent_node)
    graph.add_node("clarify", clarify_node)
    graph.add_node("search", search_node)
    graph.add_node("no_results", no_results_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("rank", rank_node)
    graph.add_node("recommend", recommend_node)

                                    
    graph.add_edge(START, "parse_intent")

                                                
    graph.add_conditional_edges(
        "parse_intent",
        route_after_intent,
        {"clarify": "clarify", "search": "search"},
    )
    graph.add_edge("clarify", END)

    graph.add_conditional_edges(
        "search",
        route_after_search,
        {"no_results": "no_results", "analyze": "analyze"},
    )
    graph.add_edge("no_results", END)

    graph.add_edge("analyze", "rank")
    graph.add_edge("rank", "recommend")
    graph.add_edge("recommend", END)

    return graph.compile()


shopping_graph = build_shopping_graph()


def _graph_config(
    *,
    session: Session,
    provider: LLMProvider,
    embedding_provider: EmbeddingProvider | None,
    stream_recommendation: bool,
) -> RunnableConfig:
    configurable: ShoppingGraphConfig = {
        "session": session,
        "provider": provider,
        "embedding_provider": embedding_provider,
        "stream_recommendation": stream_recommendation,
    }
    return {"configurable": configurable}


async def run_shopping_agent(
    *,
    session: Session,
    provider: LLMProvider,               
    message: str,             
    profile: ShoppingProfile,             
    embedding_provider: EmbeddingProvider | None = None,
) -> AgentResult:
    """Non-streaming entry point: run the full graph and return AgentResult."""
    final_state = cast(
        ShoppingGraphState,
        await shopping_graph.ainvoke(
            {"message": message, "profile": profile},
            config=_graph_config(
                session=session,
                provider=provider,
                embedding_provider=embedding_provider,
                stream_recommendation=False,
            ),
        ),
    )
    return _result_from_state(final_state)


async def stream_shopping_agent(
    *,
    session: Session,
    provider: LLMProvider,
    message: str,
    profile: ShoppingProfile,
    embedding_provider: EmbeddingProvider | None = None,
) -> AsyncIterator[AgentEvent]:
    """Streaming entry point: consume custom events emitted by nodes.

    stream_mode="custom" ignores state updates and yields only the events
    written through get_stream_writer().
    """
    config = _graph_config(
        session=session,
        provider=provider,
        embedding_provider=embedding_provider,
        stream_recommendation=True,
    )
    async for event in shopping_graph.astream(
        {"message": message, "profile": profile},
        config=config,
        stream_mode="custom",
    ):
        if isinstance(event, AgentEvent):
            yield event
