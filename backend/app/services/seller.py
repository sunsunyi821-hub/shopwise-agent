import logging
from uuid import uuid4

from sqlmodel import Session, select

from app.agent.llm import LLMProvider
from app.agent.mock import MockProvider
from app.agent.state import SellerProductDraft
from app.models import Product

logger = logging.getLogger(__name__)


async def analyze_seller_product(
    provider: LLMProvider,
    description: str,
    category: str,
    price: float,
    brand: str | None,
) -> tuple[SellerProductDraft, bool]:
    """Structure a seller description, falling back to rules on failure."""
    try:
        draft = await provider.analyze_product_description(
            description, category, price, brand
        )
        return draft, False
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Seller product analysis failed (%s), falling back to rules: %s",
            getattr(provider, "name", "unknown"),
            exc,
        )
        draft = await MockProvider().analyze_product_description(
            description, category, price, brand
        )
        return draft, True


def create_seller_product(
    session: Session,
    *,
    draft: SellerProductDraft,
    category: str,
    price: float,
    seller_id: str,
    description: str,
) -> Product:
    """Persist a structured draft; price and category stay form-authoritative."""
    product_id = f"sl-{uuid4().hex[:8]}"
    while session.get(Product, product_id) is not None:
        product_id = f"sl-{uuid4().hex[:8]}"

    brand = (draft.brand or "").strip()[:30] or "Independent seller"
    name = (draft.name or "").strip()[:40] or f"{brand} {category}"

    product = Product(
        id=product_id,
        name=name,
        brand=brand,
        category=category,
        price=price,
        original_price=None,
        rating=0.0,
        review_count=0,
        description=(draft.description or description).strip(),
        attributes=draft.attributes,
        pros=draft.pros,
        cons=draft.cons,
        tags=draft.tags,
        image_key=category,
        seller_id=seller_id,
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def list_seller_products(
    session: Session,
    seller_id: str,
    limit: int = 30,
) -> list[Product]:
    return list(
        session.exec(
            select(Product)
            .where(Product.seller_id == seller_id)
            .order_by(Product.id.desc())
            .limit(limit)
        ).all()
    )
