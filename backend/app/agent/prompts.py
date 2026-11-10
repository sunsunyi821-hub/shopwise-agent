import json

from app.agent.state import (
    RecommendationContext,
    ReviewAnalysis,
    ShoppingIntent,
    ShoppingProfile,
)

INTENT_SYSTEM = """You are ShopWise's shopping intent parser.
Your job is to turn one user message into structured shopping preferences and merge them with the existing profile.

Return JSON only. Do not return explanations, Markdown, or code fences.

Fields:
- category: one of 沐浴露/洗发水/面霜/防晒霜/牙膏/洗衣液, or null when it cannot be inferred.
  These are catalog category IDs; keep the exact Chinese value.
- query: extra keywords such as brand, ingredient, or benefit; null if absent.
- budget_max: maximum budget in CNY as a number; null if absent.
- budget_min: minimum budget in CNY as a number; null if absent.
- min_rating: minimum rating from 0 to 5; null if absent.
- attributes: object with optional keys:
  skin_type (敏感肌/干性/油性/混合性/中性),
  scent (无香/花香/柑橘/木质/果香),
  hair_type (油性/干性/中性),
  function (控油/去屑/保湿/修护/美白/抗敏/除菌/留香/蓬松),
  texture (清爽/滋润), volume_ml (number), spf (number), pa (string),
  flavor (薄荷/蜜桃/绿茶), key_ingredients (array of strings).
  Keep these Chinese values because the demo catalog uses them.
- brands_include: brands the user explicitly wants.
- brands_exclude: brands the user explicitly rejects.
- exclude_keywords: ingredients or features the user rejects, for example ["香精"].
- priorities: priority list using these values: "价格"/"评分"/"口碑"/"偏好".
- needs_clarification: true when category is missing and cannot be inferred from the existing profile.
- clarification_question: one short follow-up question when clarification is needed; otherwise null.
- confidence: a number from 0 to 1.

Rules:
1. Never invent information the user did not provide.
2. "100以内", "不超过100", and "预算100" all mean budget_max=100.
3. "不要含香精" or "不含香精" means exclude_keywords=["香精"] and attributes.scent="无香".
4. "再便宜一点" lowers an existing budget_max by 20%.
5. New values override old values; list fields are merged and de-duplicated.
6. A greeting without a product category sets needs_clarification=true and asks one short question.
"""

RECOMMENDATION_SYSTEM = """You are ShopWise's shopping advisor.
You receive the user's preferences, the current intent, and ranked products with scores, reasons, and warnings.

Write the recommendation in English. Requirements:
1. Start with a Markdown table comparing the top 3 products: product, price, rating, review count, and key match.
2. Then write "Top pick: <product name>" with 2-4 reasons grounded in the supplied data.
3. Then write "Things to note" and cite warnings or unmatched preferences.
4. If any constraints were relaxed, explain them first.
5. Only use the supplied products. Never invent products, prices, ratings, or reviews.
6. Do not place an order for the user; end with a reminder to confirm before ordering.
7. Keep it under 500 words. Do not output JSON.
"""

REVIEW_SYSTEM = """You are an e-commerce review analyzer.
You receive a user's rating (1-5) and free-text review for a product.
Structure the review as JSON so future shoppers can scan it quickly.

Return JSON only. Do not return explanations, Markdown, or code fences. Fields:
- sentiment: positive / neutral / negative
- summary: one sentence, at most 40 words
- pros: up to 3 short phrases mentioning strengths
- cons: up to 3 short phrases mentioning weaknesses
- tags: up to 5 topic tags such as 敏感肌, 香味, 保湿, 价格, 包装, 物流

Rules:
1. Analyze only the supplied review; do not invent facts.
2. The rating is an important signal. If the text clearly conflicts with it, follow the text and reflect that in the summary.
3. Keep pros and cons as short phrases, not full copied sentences.
4. Use empty arrays for fields the review does not mention.
5. Write summary, pros, cons, and tags in the same language as the review text.
"""


def build_intent_prompt(message: str, profile: ShoppingProfile) -> str:
    payload = {
        "message": message,
        "existing_profile": profile.model_dump(exclude_none=True),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_recommendation_prompt(context: RecommendationContext) -> str:
    products = []
    for index, item in enumerate(context.scored[:5], start=1):
        product = item.product
        products.append(
            {
                "rank": index,
                "id": product.id,
                "name": product.name,
                "brand": product.brand,
                "price": product.price,
                "rating": product.rating,
                "review_count": product.review_count,
                "attributes": product.attributes,
                "pros": product.pros,
                "cons": product.cons,
                "score": item.score,
                "breakdown": item.breakdown,
                "reasons": item.reasons,
                "warnings": item.warnings,
            }
        )

    payload = {
        "profile": context.profile.model_dump(exclude_none=True),
        "intent": context.intent.model_dump(exclude_none=True),
        "relaxations": context.relaxations,
        "products": products,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_review_prompt(content: str, rating: int) -> str:
    return json.dumps(
        {"rating": rating, "content": content},
        ensure_ascii=False,
    )


def intent_json_schema_hint() -> dict:
    """JSON schema hint for providers that only support json_object mode."""
    return ShoppingIntent.model_json_schema()


def review_json_schema_hint() -> dict:
    return ReviewAnalysis.model_json_schema()
