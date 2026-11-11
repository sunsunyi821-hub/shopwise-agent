from sqlmodel import Session

from app.models import Order, Product
from app.workflows.ordering import DEFAULT_ADDRESS, create_order_from_draft


def prepare_flash_draft(
    product: Product,
    *,
    quantity: int = 1,
    max_price: float | None = None,
    address: str = DEFAULT_ADDRESS,
) -> dict:
    quantity = max(1, min(5, int(quantity or 1)))
    return {
        "skill": "flash_sale",
        "product_id": product.id,
        "product_name": product.name,
        "brand": product.brand,
        "unit_price": product.price,
        "quantity": quantity,
        "total": round(product.price * quantity, 2),
        "max_price": max_price,
        "max_quantity": quantity,
        "address": address,
        "note": "Simulated flash purchase; no live marketplace or payment.",
    }


def create_flash_order(session: Session, *, user_id: str, draft: dict) -> Order:
    product = session.get(Product, str(draft["product_id"]))
    if product is None:
        raise ValueError("Product not found")
    max_price = draft.get("max_price")
    if max_price is not None and product.price > float(max_price):
        raise ValueError("Product price exceeds the flash-purchase cap")
    if int(draft["quantity"]) > int(draft.get("max_quantity") or 1):
        raise ValueError("Quantity exceeds the pre-authorized cap")
    return create_order_from_draft(session, user_id=user_id, draft=draft)
