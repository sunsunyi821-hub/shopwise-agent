import json
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.agent.prompts import (
    INTENT_SYSTEM,
    RECOMMENDATION_SYSTEM,
    REVIEW_SYSTEM,
    SELLER_PRODUCT_SYSTEM,
    build_intent_prompt,
    build_recommendation_prompt,
    build_review_prompt,
    build_seller_product_prompt,
    intent_json_schema_hint,
    review_json_schema_hint,
    seller_product_json_schema_hint,
)
from app.agent.state import (
    RecommendationContext,
    ReviewAnalysis,
    SellerProductDraft,
    ShoppingIntent,
    ShoppingProfile,
)
from app.config import Settings


def _strip_code_fence(value: str) -> str:
    value = value.strip()
    if value.startswith("```"):
        value = value.strip("`")
        if value.startswith("json"):
            value = value[4:]
    return value.strip()


class OpenAICompatibleProvider:
    name = "openai"

    def __init__(self, settings: Settings) -> None:
        api_key = settings.resolved_openai_api_key
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY / DEEPSEEK_API_KEY is empty. "
                "Set it in backend/.env or use LLM_PROVIDER=mock."
            )
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=settings.resolved_openai_base_url,
            timeout=90.0,
        )
        self.model = settings.openai_model
        self.extra_body = settings.llm_extra_body

    async def parse_intent(
        self, message: str, profile: ShoppingProfile
    ) -> ShoppingIntent:
        schema = json.dumps(intent_json_schema_hint(), ensure_ascii=False)
        messages = [
            {"role": "system", "content": INTENT_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"JSON Schema (field reference only; do not output the schema itself):\n{schema}\n\n"
                    + build_intent_prompt(message, profile)
                ),
            },
        ]
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                max_tokens=4096,
                response_format={"type": "json_object"},
                extra_body=self.extra_body,
            )
        except Exception:

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                max_tokens=4096,
                extra_body=self.extra_body,
            )

        content = response.choices[0].message.content or ""
        return ShoppingIntent.model_validate_json(_strip_code_fence(content))

    async def write_recommendation(self, context: RecommendationContext) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": RECOMMENDATION_SYSTEM},
                {
                    "role": "user",
                    "content": build_recommendation_prompt(context),
                },
            ],
            temperature=0.5,
            max_tokens=4096,
            extra_body=self.extra_body,
        )
        return (response.choices[0].message.content or "").strip()

    async def analyze_review(self, content: str, rating: int) -> ReviewAnalysis:
        schema = json.dumps(review_json_schema_hint(), ensure_ascii=False)
        messages = [
            {"role": "system", "content": REVIEW_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"JSON Schema (field reference only; do not output the schema itself):\n{schema}\n\n"
                    + build_review_prompt(content, rating)
                ),
            },
        ]
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                max_tokens=1024,
                response_format={"type": "json_object"},
                extra_body=self.extra_body,
            )
        except Exception:

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                max_tokens=1024,
                extra_body=self.extra_body,
            )

        text = response.choices[0].message.content or ""
        return ReviewAnalysis.model_validate_json(_strip_code_fence(text))

    async def analyze_product_description(
        self,
        description: str,
        category: str,
        price: float,
        brand: str | None,
    ) -> SellerProductDraft:
        schema = json.dumps(
            seller_product_json_schema_hint(), ensure_ascii=False
        )
        messages = [
            {"role": "system", "content": SELLER_PRODUCT_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"JSON Schema (field reference only; do not output the schema itself):\n{schema}\n\n"
                    + build_seller_product_prompt(
                        description, category, price, brand
                    )
                ),
            },
        ]
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=1024,
                response_format={"type": "json_object"},
                extra_body=self.extra_body,
            )
        except Exception:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=1024,
                extra_body=self.extra_body,
            )

        text = response.choices[0].message.content or ""
        return SellerProductDraft.model_validate_json(_strip_code_fence(text))

    async def stream_recommendation(
        self, context: RecommendationContext
    ) -> AsyncIterator[str]:
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": RECOMMENDATION_SYSTEM},
                {
                    "role": "user",
                    "content": build_recommendation_prompt(context),
                },
            ],
            temperature=0.5,
            max_tokens=4096,
            stream=True,
            extra_body=self.extra_body,
        )
        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
