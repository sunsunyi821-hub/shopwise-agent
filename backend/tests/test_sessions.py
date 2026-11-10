from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.agent.mock import MockProvider
from app.api import routes_chat, routes_sessions
from app.db import get_session


def make_client(db) -> TestClient:
    app = FastAPI()
    app.include_router(routes_chat.router, prefix="/api")
    app.include_router(routes_sessions.router, prefix="/api")
    app.state.provider = MockProvider()
    app.state.embedding_provider = None
    app.dependency_overrides[get_session] = lambda: db
    return TestClient(app)


def test_session_detail_returns_product_snapshot(db):
    client = make_client(db)
    response = client.post(
        "/api/chat",
        json={
            "message": "我想买一瓶沐浴露，预算 100 以内，敏感肌，最好没有香味",
            "user_id": "demo-user",
        },
    )
    assert response.status_code == 200

    body = response.json()
    detail = client.get(
        f"/api/sessions/{body['session_id']}",
        params={"user_id": "demo-user"},
    )
    assert detail.status_code == 200

    messages = detail.json()["messages"]
    assistant = next(message for message in messages if message["role"] == "assistant")
    meta = assistant["meta"]

    assert meta["provider"] == "mock"
    assert len(meta["products"]) == len(body["products"])
    assert meta["products"][0]["product"]["id"] == body["top_product_id"]
    assert "breakdown" in meta["products"][0]
    assert meta["products"][0]["reasons"]
