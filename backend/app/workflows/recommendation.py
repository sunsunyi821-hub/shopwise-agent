from collections.abc import AsyncIterator

from sqlmodel import Session

from app.agent.embeddings import EmbeddingProvider
from app.agent.llm import LLMProvider
from app.agent.orchestrator import (
    AgentResult,
    run_shopping_agent,
    stream_shopping_agent,
)
from app.agent.state import ShoppingProfile


async def run_recommendation_workflow(
    *,
    session: Session,
    provider: LLMProvider,
    message: str,
    profile: ShoppingProfile,
    embedding_provider: EmbeddingProvider | None = None,
) -> AgentResult:
    """Expose the recommendation pipeline as a supervisor tool."""
    return await run_shopping_agent(
        session=session,
        provider=provider,
        message=message,
        profile=profile,
        embedding_provider=embedding_provider,
    )


def stream_recommendation_workflow(
    *,
    session: Session,
    provider: LLMProvider,
    message: str,
    profile: ShoppingProfile,
    embedding_provider: EmbeddingProvider | None = None,
) -> AsyncIterator:
    """Streaming variant used by the chat entrypoint."""
    return stream_shopping_agent(
        session=session,
        provider=provider,
        message=message,
        profile=profile,
        embedding_provider=embedding_provider,
    )
