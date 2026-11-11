from langchain_core.tools import BaseTool, tool
from sqlmodel import Session

from app.agent.embeddings import EmbeddingProvider
from app.agent.llm import LLMProvider
from app.agent.state import ShoppingProfile
from app.mcp.client import MCPMarketplaceClient
from app.schemas import ProductOut
from app.services.catalog import get_product, list_categories
from app.workflows.flash_sale import prepare_flash_draft
from app.workflows.marketplace import run_marketplace_search_workflow
from app.workflows.ordering import prepare_order_draft
from app.workflows.recommendation import run_recommendation_workflow
from app.workflows.selling import prepare_selling_draft


def build_agent_tools(
    *,
    db: Session,
    provider: LLMProvider,
    embedding_provider: EmbeddingProvider | None,
    user_id: str,
    mcp_client: MCPMarketplaceClient | None = None,
) -> dict[str, BaseTool]:
    """Wrap workflows as agent tools; dependencies are injected by closure."""

    @tool
    async def recommend_products(request: str) -> dict:
        """Run the full product recommendation workflow for a shopping request."""
        result = await run_recommendation_workflow(
            session=db,
            provider=provider,
            message=request,
            profile=ShoppingProfile(),
            embedding_provider=embedding_provider,
        )
        return {
            "recommendation": result.recommendation,
            "clarification": result.clarification,
            "top_product_id": result.top_product_id,
            "needs_clarification": bool(result.clarification),
            "products": [
                {
                    "product": ProductOut.model_validate(item.product).model_dump(
                        mode="json"
                    ),
                    "score": item.score,
                    "breakdown": item.breakdown,
                    "reasons": item.reasons,
                    "warnings": item.warnings,
                }
                for item in result.scored
            ],
        }

    @tool
    async def prepare_order(product_id: str, quantity: int = 1) -> dict:
        """Create an order draft for a selected product; never places the order."""
        product = get_product(db, product_id)
        if product is None:
            return {"error": "Product not found"}
        return {"draft": prepare_order_draft(product, quantity=quantity)}

    @tool
    async def prepare_selling(
        description: str,
        category: str,
        price: float,
        brand: str | None = None,
    ) -> dict:
        """Create a seller listing draft; never publishes without confirmation."""
        if category not in list_categories(db):
            return {"error": "Unknown category"}
        if price <= 0:
            return {"error": "Price must be greater than zero"}
        draft, degraded = await prepare_selling_draft(
            provider,
            description=description,
            category=category,
            price=price,
            brand=brand,
            seller_id=user_id,
        )
        return {"draft": draft, "degraded": degraded}

    @tool
    async def prepare_flash_sale(
        product_id: str,
        quantity: int = 1,
        max_price: float | None = None,
    ) -> dict:
        """Create a flash-purchase draft; never places the order."""
        product = get_product(db, product_id)
        if product is None:
            return {"error": "Product not found"}
        return {
            "draft": prepare_flash_draft(
                product,
                quantity=quantity,
                max_price=max_price,
            )
        }

    tools: dict[str, BaseTool] = {
        "recommend_products": recommend_products,
        "prepare_order": prepare_order,
        "prepare_selling": prepare_selling,
        "prepare_flash_sale": prepare_flash_sale,
    }

    if mcp_client is not None and mcp_client.enabled:

        @tool
        async def search_external_marketplace(
            query: str,
            platforms: list[str],
            category: str | None = None,
            budget_max: float | None = None,
            limit: int = 3,
        ) -> dict:
            """Search JD/Taobao through MCP and compare price, rating, and review volume."""
            result = await run_marketplace_search_workflow(
                client=mcp_client,
                goal=query,
                args={
                    "query": query,
                    "platforms": platforms,
                    "category": category,
                    "budget_max": budget_max,
                    "limit": limit,
                },
            )
            return result.model_dump(mode="json")

        tools["search_external_marketplace"] = search_external_marketplace

    return tools
