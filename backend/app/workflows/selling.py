from sqlmodel import Session

from app.agent.llm import LLMProvider
from app.agent.state import SellerProductDraft
from app.models import Product
from app.services.seller import (
    analyze_seller_product,
    create_seller_product,
    list_seller_products,
)


async def prepare_selling_draft(
    provider: LLMProvider,
    *,
    description: str,
    category: str,
    price: float,
    brand: str | None,
    seller_id: str,
) -> tuple[dict, bool]:
    draft, degraded = await analyze_seller_product(
        provider,
        description,
        category,
        price,
        brand,
    )
    return (
        {
            "skill": "sell",
            "draft": draft.model_dump(),
            "category": category,
            "price": float(price),
            "seller_id": seller_id,
            "description": description,
            "degraded": degraded,
        },
        degraded,
    )


def create_product_from_draft(
    session: Session,
    *,
    user_id: str,
    draft: dict,
) -> Product:
    product_draft = SellerProductDraft.model_validate(draft["draft"])
    return create_seller_product(
        session,
        draft=product_draft,
        category=str(draft["category"]),
        price=float(draft["price"]),
        seller_id=user_id,
        description=str(draft["description"]),
    )


__all__ = [
    "prepare_selling_draft",
    "create_product_from_draft",
    "list_seller_products",
]
