import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.agent.mock import MockProvider
from app.api import routes_products, routes_seller
from app.db import get_session
from app.services.seller import analyze_seller_product


class FailingSellerProvider:
    name = "failing"

    async def analyze_product_description(
        self,
        description: str,
        category: str,
        price: float,
        brand: str | None,
    ):
        raise RuntimeError("llm unavailable")


def make_client(db) -> TestClient:
    app = FastAPI()
    app.include_router(routes_products.router, prefix="/api")
    app.include_router(routes_seller.router, prefix="/api")
    app.state.provider = MockProvider()
    app.dependency_overrides[get_session] = lambda: db
    return TestClient(app)


SELLER_PAYLOAD = {
    "description": (
        "这是一款温和的氨基酸沐浴露，适合敏感肌，香味很淡，"
        "泡沫细腻，洗完不紧绷。注意泵头偏紧。"
    ),
    "price": 69,
    "category": "沐浴露",
    "brand": "Test Brand",
    "seller_id": "seller-1",
}


@pytest.mark.asyncio
async def test_mock_seller_product_analysis_extracts_structure():
    draft = await MockProvider().analyze_product_description(
        SELLER_PAYLOAD["description"],
        "沐浴露",
        69,
        "Test Brand",
    )
    assert "Test Brand" in draft.name
    assert draft.brand == "Test Brand"
    assert draft.attributes["skin_type"] == "敏感肌"
    assert "沐浴露" in draft.tags
    assert draft.description


@pytest.mark.asyncio
async def test_seller_analysis_falls_back_when_llm_fails():
    draft, degraded = await analyze_seller_product(
        FailingSellerProvider(),
        SELLER_PAYLOAD["description"],
        "沐浴露",
        69,
        "Test Brand",
    )
    assert degraded is True
    assert draft.name


def test_seller_product_api_flow(db):
    client = make_client(db)

    response = client.post("/api/seller/products", json=SELLER_PAYLOAD)
    assert response.status_code == 201
    body = response.json()
    product = body["product"]
    assert product["seller_id"] == "seller-1"
    assert product["category"] == "沐浴露"
    assert product["price"] == 69
    assert product["rating"] == 0
    assert product["review_count"] == 0
    assert product["name"]
    assert body["degraded"] is False

    listed = client.get(
        "/api/seller/products",
        params={"seller_id": "seller-1"},
    )
    assert listed.status_code == 200
    assert any(item["id"] == product["id"] for item in listed.json())

    catalog = client.get(
        "/api/products",
        params={"category": "沐浴露", "limit": 200},
    )
    assert catalog.status_code == 200
    assert any(item["id"] == product["id"] for item in catalog.json()["products"])

    invalid = client.post(
        "/api/seller/products",
        json={**SELLER_PAYLOAD, "category": "not-a-category"},
    )
    assert invalid.status_code == 400
