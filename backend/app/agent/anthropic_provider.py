from collections.abc import AsyncIterator

from anthropic import AsyncAnthropic

from app.agent.prompts import (
    INTENT_SYSTEM,
    PLANNER_SYSTEM,
    RECOMMENDATION_SYSTEM,
    REVIEW_SYSTEM,
    SELLER_PRODUCT_SYSTEM,
    build_intent_prompt,
    build_plan_prompt,
    build_recommendation_prompt,
    build_review_prompt,
    build_seller_product_prompt,
)
from app.agent.state import (
    AgentPlan,
    RecommendationContext,
    ReviewAnalysis,
    SellerProductDraft,
    ShoppingIntent,
    ShoppingProfile,
)
from app.config import Settings


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, settings: Settings) -> None:
        if not settings.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is empty. Set it in backend/.env or use LLM_PROVIDER=mock."
            )
        kwargs: dict = {"api_key": settings.anthropic_api_key, "timeout": 90.0}
        if settings.anthropic_base_url:
            kwargs["base_url"] = settings.anthropic_base_url
        self.client = AsyncAnthropic(**kwargs)
        self.model = settings.llm_model

    async def parse_intent(
        self, message: str, profile: ShoppingProfile
    ) -> ShoppingIntent:
        response = await self.client.messages.parse(
            model=self.model,
            max_tokens=4096,
            system=INTENT_SYSTEM,
            messages=[{"role": "user", "content": build_intent_prompt(message, profile)}],
            output_format=ShoppingIntent,
            output_config={"effort": "low"},
        )
        if response.parsed_output is None:
            raise ValueError("Anthropic returned no parsed intent")
        return response.parsed_output

    async def write_recommendation(self, context: RecommendationContext) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=RECOMMENDATION_SYSTEM,
            messages=[
                {"role": "user", "content": build_recommendation_prompt(context)}
            ],
            output_config={"effort": "low"},
        )
        if response.stop_reason == "refusal":
            return "The model refused this recommendation request. Please rephrase and try again."
        return "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()

    async def analyze_review(self, content: str, rating: int) -> ReviewAnalysis:
        response = await self.client.messages.parse(
            model=self.model,
            max_tokens=1024,
            system=REVIEW_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": build_review_prompt(content, rating),
                }
            ],
            output_format=ReviewAnalysis,
            output_config={"effort": "low"},
        )
        if response.parsed_output is None:
            raise ValueError("Anthropic returned no parsed review analysis")
        return response.parsed_output

    async def plan_tasks(self, goal: str) -> AgentPlan:
        response = await self.client.messages.parse(
            model=self.model,
            max_tokens=1024,
            system=PLANNER_SYSTEM,
            messages=[
                {"role": "user", "content": build_plan_prompt(goal)}
            ],
            output_format=AgentPlan,
            output_config={"effort": "low"},
        )
        if response.parsed_output is None:
            raise ValueError("Anthropic returned no parsed task plan")
        return response.parsed_output

    async def analyze_product_description(
        self,
        description: str,
        category: str,
        price: float,
        brand: str | None,
    ) -> SellerProductDraft:
        response = await self.client.messages.parse(
            model=self.model,
            max_tokens=1024,
            system=SELLER_PRODUCT_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": build_seller_product_prompt(
                        description, category, price, brand
                    ),
                }
            ],
            output_format=SellerProductDraft,
            output_config={"effort": "low"},
        )
        if response.parsed_output is None:
            raise ValueError("Anthropic returned no parsed product draft")
        return response.parsed_output

    async def stream_recommendation(
        self, context: RecommendationContext
    ) -> AsyncIterator[str]:
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=4096,
            system=RECOMMENDATION_SYSTEM,
            messages=[
                {"role": "user", "content": build_recommendation_prompt(context)}
            ],
            output_config={"effort": "low"},
        ) as stream:
            async for text in stream.text_stream:
                yield text
