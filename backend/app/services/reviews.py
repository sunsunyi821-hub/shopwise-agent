import logging
from datetime import UTC, datetime

from sqlmodel import Session, select

from app.agent.llm import LLMProvider
from app.agent.mock import MockProvider
from app.agent.state import ReviewAnalysis
from app.models import Order, Product, Review

logger = logging.getLogger(__name__)


async def analyze_review(
    provider: LLMProvider,
    content: str,
    rating: int,
) -> tuple[ReviewAnalysis, bool]:
    """Run LLM analysis, falling back to rule-based analysis on failure."""
    try:
        return await provider.analyze_review(content, rating), False
    except Exception as exc:
        logger.warning(
            "Review analysis failed (%s), falling back to rules: %s",
            getattr(provider, "name", "unknown"),
            exc,
        )
        return await MockProvider().analyze_review(content, rating), True


def get_review_by_order(session: Session, order_id: str) -> Review | None:
    return session.exec(select(Review).where(Review.order_id == order_id)).first()


def create_review(
    session: Session,
    *,
    order: Order,
    rating: int,
    content: str,
    author: str,
    user_id: str,
    analysis: ReviewAnalysis,
) -> Review:
    review = Review(
        product_id=order.product_id,
        rating=rating,
        content=content,
        author=author or "Anonymous",
        user_id=user_id,
        order_id=order.id,
        sentiment=analysis.sentiment,
        summary=analysis.summary,
        pros=analysis.pros,
        cons=analysis.cons,
        tags=analysis.tags,
    )
    session.add(review)



    product = session.get(Product, order.product_id)
    if product is not None:
        old_count = max(0, product.review_count)
        product.rating = round(
            (product.rating * old_count + rating) / (old_count + 1),
            2,
        )
        product.review_count = old_count + 1
        session.add(product)

    session.commit()
    session.refresh(review)
    return review


def update_review(
    session: Session,
    *,
    review: Review,
    rating: int,
    content: str,
    author: str | None,
    analysis: ReviewAnalysis,
) -> Review:
    old_rating = review.rating
    review.rating = rating
    review.content = content
    if author:
        review.author = author
    review.sentiment = analysis.sentiment
    review.summary = analysis.summary
    review.pros = analysis.pros
    review.cons = analysis.cons
    review.tags = analysis.tags
    review.updated_at = datetime.now(UTC)
    session.add(review)


    product = session.get(Product, review.product_id)
    if product is not None and product.review_count > 0:
        product.rating = round(
            (
                product.rating * product.review_count
                - old_rating
                + rating
            )
            / product.review_count,
            2,
        )
        session.add(product)

    session.commit()
    session.refresh(review)
    return review


def list_reviews(
    session: Session,
    product_id: str,
    limit: int = 20,
) -> list[Review]:
    return list(
        session.exec(
            select(Review)
            .where(Review.product_id == product_id)
            .order_by(Review.updated_at.desc(), Review.id.desc())
            .limit(limit)
        ).all()
    )
