from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.db import get_session
from app.models import Order, Review
from app.schemas import OrderCreate, OrderOut
from app.services.catalog import get_product

router = APIRouter(prefix="/orders", tags=["orders"])


def _reviewed_order_ids(db: Session, orders: list[Order]) -> set[str]:
    order_ids = [order.id for order in orders]
    if not order_ids:
        return set()
    reviewed = db.exec(
        select(Review.order_id).where(Review.order_id.in_(order_ids))
    ).all()
    return {order_id for order_id in reviewed if order_id}


@router.post("", response_model=OrderOut, status_code=201)
                            
                           
     
         
                  
     
     
      
     
      
     
    
      
     
         
              
     
     
         
              
     
     
       
       
def create_order(                                       
    payload: OrderCreate, db: Session = Depends(get_session)
) -> OrderOut:
    if not payload.confirm:
        raise HTTPException(
            status_code=400,
            detail="Order confirmation is required (confirm=true). The agent never places an order automatically.",
        )

    product = get_product(db, payload.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    unit_price = product.price
    total_price = round(unit_price * payload.quantity, 2)
                   
                    
    order = Order(
        id=f"SW-{datetime.now(UTC):%Y%m%d}-{uuid4().hex[:6].upper()}",
                            
        user_id=payload.user_id,
        session_id=payload.session_id,
        product_id=product.id,
        product_name=product.name,
        quantity=payload.quantity,
        unit_price=unit_price,
        total_price=total_price,
        status="confirmed",
        address=payload.address,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return OrderOut.model_validate(order)


@router.get("", response_model=list[OrderOut])
def list_orders(       
    user_id: str = Query(default="demo-user"),
                                            
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_session),
) -> list[OrderOut]:
    orders = list(
        db.exec(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())                 
            .limit(limit)             
        ).all()
    )
    reviewed = _reviewed_order_ids(db, orders)
    return [
        OrderOut.model_validate(order).model_copy(
            update={"reviewed": order.id in reviewed}
        )
        for order in orders
    ]


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: str,
    user_id: str = Query(default="demo-user"),
    db: Session = Depends(get_session),
) -> OrderOut:
    order = db.get(Order, order_id)
                  
    if order is None or order.user_id != user_id:
        raise HTTPException(status_code=404, detail="Order not found")
    reviewed = (
        db.exec(select(Review.id).where(Review.order_id == order.id)).first()
        is not None
    )
    return OrderOut.model_validate(order).model_copy(
        update={"reviewed": reviewed}
    )
