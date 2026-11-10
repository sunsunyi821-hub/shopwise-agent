from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session

from app.db import get_session
from app.schemas import (
    ProductOut,
    SellerProductCreate,
    SellerProductCreatedOut,
)
from app.services.catalog import list_categories
from app.services.seller import (
    analyze_seller_product,
    create_seller_product,
    list_seller_products,
)

router = APIRouter(prefix="/seller", tags=["seller"])


@router.post("/products", response_model=SellerProductCreatedOut, status_code=201)
async def create_product(
    payload: SellerProductCreate,
    request: Request,
    db: Session = Depends(get_session),
) -> SellerProductCreatedOut:
    if payload.category not in list_categories(db):
        raise HTTPException(status_code=400, detail="Unknown category")

    provider = request.app.state.provider
    draft, degraded = await analyze_seller_product(
        provider,
        payload.description,
        payload.category,
        payload.price,
        payload.brand,
    )
    product = create_seller_product(
        db,
        draft=draft,
        category=payload.category,
        price=payload.price,
        seller_id=payload.seller_id,
        description=payload.description,
    )
    return SellerProductCreatedOut(
        product=ProductOut.model_validate(product),
        degraded=degraded,
    )


@router.get("/products", response_model=list[ProductOut])
def my_products(
    seller_id: str = Query(default="demo-seller"),
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_session),
) -> list[ProductOut]:
    return [
        ProductOut.model_validate(product)
        for product in list_seller_products(db, seller_id, limit)
    ]
