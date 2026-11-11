from pydantic import BaseModel, Field


class MarketplaceProduct(BaseModel):
    """Normalized external product returned by an MCP marketplace tool."""

    id: str
    platform: str
    platform_label: str
    name: str
    brand: str
    category: str
    price: float
    original_price: float | None = None
    rating: float
    review_count: int
    sales: int = 0
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    image_key: str = ""
    url: str = ""
    value_score: float = 0.0
    reasons: list[str] = Field(default_factory=list)


class MarketplaceToolCall(BaseModel):
    """One MCP tools/call, surfaced in the UI as an execution trace."""

    name: str
    arguments: dict = Field(default_factory=dict)
    ok: bool = True
    duration_ms: int = 0
    error: str | None = None


class MarketplaceSearchResult(BaseModel):
    query: str
    platforms: list[str] = Field(default_factory=list)
    budget_max: float | None = None
    products: list[MarketplaceProduct] = Field(default_factory=list)
    recommendation: str = ""
    tool_calls: list[MarketplaceToolCall] = Field(default_factory=list)
    note: str = "MCP demo data; no live marketplace or payment connection."
