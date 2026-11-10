from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.db import get_session
from app.schemas import ProductListResponse, ProductOut
from app.services.catalog import get_product, list_catalog, list_categories

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductListResponse)
def list_products(
    category: str | None = None,
    max_price: float | None = Query(default=None, ge=0),
    min_rating: float | None = Query(default=None, ge=0, le=5),
    q: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> ProductListResponse:
    products = list_catalog(
        session,
        category=category,
        max_price=max_price,
        min_rating=min_rating,
        q=q,
        limit=limit,
    )
    return ProductListResponse(
        products=[ProductOut.model_validate(product) for product in products],
        total=len(products),
    )


@router.get("/categories", response_model=list[str])
def categories(session: Session = Depends(get_session)) -> list[str]:
    return list_categories(session)


@router.get("/{product_id}", response_model=ProductOut)
def product_detail(
    product_id: str, session: Session = Depends(get_session)
) -> ProductOut:
    product = get_product(session, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductOut.model_validate(product)
