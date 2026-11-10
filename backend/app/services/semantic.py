import hashlib
import logging
from datetime import UTC, datetime

from sqlmodel import Session, select

from app.agent.embeddings import EmbeddingProvider, cosine_similarity
from app.agent.state import ShoppingProfile
from app.models import Product, ProductEmbedding

logger = logging.getLogger(__name__)


def product_text(product: Product) -> str:
    """The text we embed for a product.

    Keep this deterministic: if it changes, the stored text_hash changes and the
    embedding is recomputed on the next startup.
    """
    attribute_text = " ".join(str(value) for value in product.attributes.values())
    return " ".join(
        [
            product.name,
            product.brand,
            product.category,
            product.description,
            " ".join(product.tags),
            attribute_text,
            " ".join(product.pros),
            " ".join(product.cons),
        ]
    ).strip()


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_query_text(message: str, profile: ShoppingProfile) -> str:
    parts = [
        message,
        profile.category or "",
        profile.query or "",
        " ".join(str(value) for value in profile.attributes.values()),
        " ".join(profile.priorities),
        " ".join(profile.brands_include),
    ]
    return " ".join(part for part in parts if part).strip()


async def ensure_embeddings(session: Session, provider: EmbeddingProvider) -> int:
    """Create or refresh product embeddings. Returns the number of products embedded."""
    products = list(session.exec(select(Product)).all())
    if not products:
        return 0

    existing = {
        item.product_id: item
        for item in session.exec(
            select(ProductEmbedding).where(ProductEmbedding.model == provider.model)
        ).all()
    }

    pending: list[tuple[Product, str, str]] = []
    for product in products:
        text = product_text(product)
        digest = text_hash(text)
        cached = existing.get(product.id)
        if cached is None or cached.text_hash != digest:
            pending.append((product, text, digest))

    if not pending:
        return 0

    try:
        vectors = await provider.embed([text for _, text, _ in pending])
    except Exception as exc:                                         
        logger.warning("Failed to create product embeddings: %s", exc)
        raise

    for (product, _, digest), vector in zip(pending, vectors, strict=True):
        cached = session.get(ProductEmbedding, product.id)
        if cached is None:
            session.add(
                ProductEmbedding(
                    product_id=product.id,
                    model=provider.model,
                    text_hash=digest,
                    vector=vector,
                )
            )
        else:
            cached.model = provider.model
            cached.text_hash = digest
            cached.vector = vector
            cached.updated_at = datetime.now(UTC)
            session.add(cached)

    session.commit()
    logger.info("Embedded %s products with %s", len(pending), provider.model)
    return len(pending)


async def compute_semantic_scores(
    session: Session,
    provider: EmbeddingProvider,
    query_text: str,
) -> dict[str, float]:
    """Cosine similarity between the query and every cached product embedding."""
    if not query_text:
        return {}

    rows = list(
        session.exec(
            select(ProductEmbedding).where(ProductEmbedding.model == provider.model)
        ).all()
    )
    if not rows:
        return {}

    try:
        query_vector = (await provider.embed([query_text]))[0]
    except Exception as exc:                                                            
        logger.warning("Query embedding failed: %s", exc)
        return {}

    return {
        row.product_id: cosine_similarity(query_vector, row.vector)
        for row in rows
    }
