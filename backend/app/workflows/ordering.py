from datetime import UTC, datetime
from uuid import uuid4

from sqlmodel import Session

from app.models import Order, Product

DEFAULT_ADDRESS = "1 Demo Road, Shanghai"


def prepare_order_draft(
    product: Product,
    *,
    quantity: int = 1,
    address: str = DEFAULT_ADDRESS,
    max_price: float | None = None,
) -> dict:
    quantity = max(1, min(5, int(quantity or 1)))
    return {
        "skill": "order",
        "product_id": product.id,
        "product_name": product.name,
        "brand": product.brand,
        "unit_price": product.price,
        "quantity": quantity,
        "total": round(product.price * quantity, 2),
        "address": address,
        "max_price": max_price,
    }


def create_order_from_draft(session: Session, *, user_id: str, draft: dict) -> Order:
    product = session.get(Product, str(draft["product_id"]))
    if product is None:
        raise ValueError("Product not found")
    if abs(product.price - float(draft["unit_price"])) > 0.01:
        raise ValueError("Product price changed; please replan")
    quantity = int(draft["quantity"])
    order = Order(
        id=f"SW-{datetime.now(UTC):%Y%m%d}-{uuid4().hex[:6].upper()}",
        user_id=user_id,
        session_id=None,
        product_id=product.id,
        product_name=product.name,
        quantity=quantity,
        unit_price=product.price,
        total_price=round(product.price * quantity, 2),
        status="confirmed",
        address=str(draft["address"]),
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return order
