from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session

from app.db import get_session
from app.models import Order, Review
from app.schemas import ReviewCreate, ReviewCreatedOut, ReviewOut, ReviewUpdate
from app.services.catalog import get_product
from app.services.reviews import (
    analyze_review,
    create_review,
    get_review_by_order,
    list_reviews,
    update_review,
)

router = APIRouter(tags=["reviews"])


@router.post("/reviews", response_model=ReviewCreatedOut, status_code=201)
async def submit_review(
    payload: ReviewCreate,
    request: Request,
    db: Session = Depends(get_session),
) -> ReviewCreatedOut:
    order = db.get(Order, payload.order_id)
    if order is None or order.user_id != payload.user_id:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status == "cancelled":
        raise HTTPException(status_code=400, detail="Cannot review a cancelled order")
    if get_review_by_order(db, order.id) is not None:
        raise HTTPException(status_code=409, detail="This order has already been reviewed")
    if get_product(db, order.product_id) is None:
        raise HTTPException(status_code=404, detail="Product not found")

    provider = request.app.state.provider
    analysis, degraded = await analyze_review(
        provider,
        payload.content,
        payload.rating,
    )
    review = create_review(
        db,
        order=order,
        rating=payload.rating,
        content=payload.content,
        author=payload.author,
        user_id=payload.user_id,
        analysis=analysis,
    )
    return ReviewCreatedOut(
        **ReviewOut.model_validate(review).model_dump(),
        degraded=degraded,
    )


@router.get("/orders/{order_id}/review", response_model=ReviewOut)
def order_review(
    order_id: str,
    user_id: str = Query(default="demo-user"),
    db: Session = Depends(get_session),
) -> ReviewOut:
    order = db.get(Order, order_id)
    if order is None or order.user_id != user_id:
        raise HTTPException(status_code=404, detail="Order not found")
    review = get_review_by_order(db, order.id)
    if review is None:
        raise HTTPException(status_code=404, detail="This order has no review yet")
    return ReviewOut.model_validate(review)


@router.put("/reviews/{review_id}", response_model=ReviewCreatedOut)
async def edit_review(
    review_id: int,
    payload: ReviewUpdate,
    request: Request,
    db: Session = Depends(get_session),
) -> ReviewCreatedOut:
    review = db.get(Review, review_id)
    if review is None or review.user_id != payload.user_id or review.order_id is None:
        raise HTTPException(status_code=404, detail="Review not found")
    order = db.get(Order, review.order_id)
    if order is None or order.user_id != payload.user_id:
        raise HTTPException(status_code=404, detail="Review not found")

    provider = request.app.state.provider
    analysis, degraded = await analyze_review(
        provider,
        payload.content,
        payload.rating,
    )
    updated = update_review(
        db,
        review=review,
        rating=payload.rating,
        content=payload.content,
        author=payload.author,
        analysis=analysis,
    )
    return ReviewCreatedOut(
        **ReviewOut.model_validate(updated).model_dump(),
        degraded=degraded,
    )


@router.get("/products/{product_id}/reviews", response_model=list[ReviewOut])
def product_reviews(
    product_id: str,
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_session),
) -> list[ReviewOut]:
    if get_product(db, product_id) is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return [
        ReviewOut.model_validate(review)
        for review in list_reviews(db, product_id, limit=limit)
    ]
