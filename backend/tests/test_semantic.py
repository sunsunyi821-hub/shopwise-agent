import pytest

from app.agent.embeddings import MockEmbeddingProvider
from app.agent.mock import MockProvider
from app.agent.orchestrator import run_shopping_agent
from app.agent.state import ShoppingProfile
from app.models import Product
from app.services.ranking import rank_products
from app.services.semantic import (
    build_query_text,
    compute_semantic_scores,
    ensure_embeddings,
)


def make_product(id: str, price: float, rating: float, reviews: int) -> Product:
    return Product(
        id=id,
        name=f"测试商品{id}",
        brand="测试",
        category="沐浴露",
        price=price,
        rating=rating,
        review_count=reviews,
        attributes={},
        pros=[],
        cons=[],
        tags=[],
        image_key=id,
    )


@pytest.mark.asyncio
async def test_semantic_scores_prefer_matching_product(db):
    provider = MockEmbeddingProvider()
    count = await ensure_embeddings(db, provider)
    assert count == 36

    profile = ShoppingProfile(
        category="沐浴露",
        attributes={"skin_type": "敏感肌", "scent": "无香"},
    )
    query = build_query_text("敏感肌 无香 沐浴露", profile)
    scores = await compute_semantic_scores(db, provider, query)

    assert scores
    assert scores["bw-001"] > scores["ld-001"]


def test_ranking_uses_semantic_score_when_available():
    products = [
                                                                                 
        make_product(id="a", price=50, rating=4.5, reviews=1000),
        make_product(id="b", price=50, rating=4.5, reviews=1000),
    ]
    profile = ShoppingProfile(category="沐浴露")

    without_semantic = rank_products(products, profile)
    assert "semantic" not in without_semantic[0].breakdown

    with_semantic = rank_products(
        products, profile, semantic_scores={"a": 0.2, "b": 0.9}
    )
    assert with_semantic[0].product.id == "b"
    assert "semantic" in with_semantic[0].breakdown
    assert with_semantic[0].breakdown["semantic"] == 0.9


class FailingEmbeddingProvider:
    model = "failing"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("embedding endpoint unavailable")


@pytest.mark.asyncio
async def test_agent_survives_embedding_failure(db):
    result = await run_shopping_agent(
        session=db,
        provider=MockProvider(),
        message="我想买一瓶沐浴露，预算 100 以内",
        profile=ShoppingProfile(),
        embedding_provider=FailingEmbeddingProvider(),
    )

    assert result.scored
    assert "semantic" not in result.scored[0].breakdown
