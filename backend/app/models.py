from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class Product(SQLModel, table=True):


    __tablename__ = "products"

    id: str = Field(primary_key=True)


    name: str = Field(index=True)

    brand: str = Field(index=True)
    category: str = Field(index=True)

    price: float = Field(index=True)
    original_price: float | None = None
    rating: float = Field(default=0.0, index=True)
    review_count: int = 0
    description: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))




    pros: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    cons: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    image_key: str = "default"
    seller_id: str | None = Field(default=None, index=True)


class Review(SQLModel, table=True):
    __tablename__ = "reviews"

    id: int | None = Field(default=None, primary_key=True)


    product_id: str = Field(index=True, foreign_key="products.id")

    rating: int = 5
    content: str = ""
    author: str = "Anonymous"


    user_id: str | None = Field(default=None, index=True)
    order_id: str | None = Field(default=None, index=True)


    sentiment: str = "neutral"
    summary: str = ""
    pros: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    cons: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ProductEmbedding(SQLModel, table=True):
    """Cached embedding for semantic product retrieval."""

    __tablename__ = "product_embeddings"

    product_id: str = Field(primary_key=True, foreign_key="products.id")
    model: str = Field(index=True)
    text_hash: str
    vector: list[float] = Field(default_factory=list, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=utc_now)


class AgentTask(SQLModel, table=True):
    """Supervisor task with plan, results, and a pending confirmation draft."""

    __tablename__ = "agent_tasks"

    id: str = Field(primary_key=True)
    user_id: str = Field(index=True)
    goal: str
    status: str = "planned"
    risk: str = "read"
    plan: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    results: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    draft: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_sessions"

    id: str = Field(primary_key=True)
    user_id: str = Field(index=True)
    title: str = "New shopping chat"
    profile: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"

    id: int | None = Field(default=None, primary_key=True)
    session_id: str = Field(index=True, foreign_key="chat_sessions.id")
    role: str = "user"

    content: str = ""
    meta: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)


class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: str = Field(primary_key=True)
    user_id: str = Field(index=True)
    session_id: str | None = Field(default=None, index=True)
    product_id: str
    product_name: str
    quantity: int = 1
    unit_price: float
    total_price: float
    status: str = "confirmed"
    address: str = ""
    created_at: datetime = Field(default_factory=utc_now)
