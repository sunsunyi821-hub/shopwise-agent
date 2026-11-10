import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.agent.mock import MockProvider
from app.api import routes_orders, routes_products, routes_reviews
from app.db import get_session
from app.models import Order, Product
from app.services.reviews import analyze_review, create_review

ORDER_PAYLOAD = {
    "product_id": "bw-001",
    "quantity": 1,
    "address": "上海市浦东新区演示路 1 号",
    "user_id": "demo-user",
    "confirm": True,
}

REVIEW_PAYLOAD = {
    "rating": 5,
    "content": "用了两周，敏感肌没有刺激，香味很淡，会回购",
    "author": "测试用户",
    "user_id": "demo-user",
}


class FailingReviewProvider:
    name = "failing"

    async def analyze_review(self, content: str, rating: int):
        raise RuntimeError("llm unavailable")


def make_client(db) -> TestClient:
    app = FastAPI()
    app.include_router(routes_orders.router, prefix="/api")
    app.include_router(routes_products.router, prefix="/api")
    app.include_router(routes_reviews.router, prefix="/api")
    app.state.provider = MockProvider()
    app.dependency_overrides[get_session] = lambda: db
    return TestClient(app)


@pytest.mark.asyncio
async def test_mock_review_analysis_extracts_structure():
    analysis = await MockProvider().analyze_review(
        "用了两周，敏感肌没有刺激，香味很淡，会回购",
        5,
    )
    assert analysis.sentiment == "positive"
    assert analysis.summary
    assert "会回购" in analysis.pros
    assert analysis.cons == []
    assert "敏感肌" in analysis.tags
    assert "香味" in analysis.tags


@pytest.mark.asyncio
async def test_review_analysis_falls_back_when_llm_fails():
    analysis, degraded = await analyze_review(
        FailingReviewProvider(),
        "很好用，会回购",
        5,
    )
    assert degraded is True
    assert analysis.sentiment == "positive"
    assert analysis.summary


@pytest.mark.asyncio
async def test_create_review_updates_product_aggregate(db):
    product = db.get(Product, "bw-001")
    assert product is not None
    old_rating = product.rating
    old_count = product.review_count

    order = Order(
        id="SW-TEST-0001",
        user_id="demo-user",
        product_id=product.id,
        product_name=product.name,
        quantity=1,
        unit_price=product.price,
        total_price=product.price,
        status="confirmed",
        address="上海市浦东新区演示路 1 号",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    analysis = await MockProvider().analyze_review("很好用，会回购", 5)
    review = create_review(
        db,
        order=order,
        rating=5,
        content="很好用，会回购",
        author="测试用户",
        user_id="demo-user",
        analysis=analysis,
    )

    assert review.id is not None
    db.refresh(product)
    assert product.review_count == old_count + 1
    assert product.rating >= old_rating


def test_review_api_flow(db):
    client = make_client(db)

    order_response = client.post("/api/orders", json=ORDER_PAYLOAD)
    assert order_response.status_code == 201
    order = order_response.json()
    assert order["reviewed"] is False

    review_response = client.post(
        "/api/reviews",
        json={"order_id": order["id"], **REVIEW_PAYLOAD},
    )
    assert review_response.status_code == 201
    review = review_response.json()
    assert review["order_id"] == order["id"]
    assert review["sentiment"] == "positive"
    assert review["summary"]
    assert review["degraded"] is False

    duplicate = client.post(
        "/api/reviews",
        json={"order_id": order["id"], **REVIEW_PAYLOAD},
    )
    assert duplicate.status_code == 409

    review_detail = client.get(
        f"/api/orders/{order['id']}/review",
        params={"user_id": "demo-user"},
    )
    assert review_detail.status_code == 200
    assert review_detail.json()["id"] == review["id"]

    product_before = client.get("/api/products/bw-001").json()
    updated_response = client.put(
        f"/api/reviews/{review['id']}",
        json={
            "rating": 3,
            "content": "用了一个月，香味太淡，泵头还是偏紧，不会回购。",
            "author": "测试用户",
            "user_id": "demo-user",
        },
    )
    assert updated_response.status_code == 200
    updated = updated_response.json()
    assert updated["rating"] == 3
    assert updated["summary"] != review["summary"]
    assert updated["updated_at"]

    product_after = client.get("/api/products/bw-001").json()
    assert product_after["review_count"] == product_before["review_count"]

    forbidden = client.put(
        f"/api/reviews/{review['id']}",
        json={
            "rating": 4,
            "content": "越权修改评价",
            "user_id": "other-user",
        },
    )
    assert forbidden.status_code == 404

    order_detail = client.get(
        f"/api/orders/{order['id']}",
        params={"user_id": "demo-user"},
    )
    assert order_detail.status_code == 200
    assert order_detail.json()["reviewed"] is True

    order_list = client.get("/api/orders", params={"user_id": "demo-user"})
    assert order_list.status_code == 200
    listed = next(item for item in order_list.json() if item["id"] == order["id"])
    assert listed["reviewed"] is True

    reviews = client.get(f"/api/products/{order['product_id']}/reviews")
    assert reviews.status_code == 200
    assert any(item["id"] == review["id"] for item in reviews.json())
