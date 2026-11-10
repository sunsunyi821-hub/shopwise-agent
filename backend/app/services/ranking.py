import math
from typing import Any

from app.agent.state import ScoredProduct, ShoppingProfile
from app.models import Product

DEFAULT_WEIGHTS = {
    "price": 0.25,
    "rating": 0.25,
    "reviews": 0.10,
    "preference": 0.20,
    "semantic": 0.20,
}

ATTRIBUTE_LABELS = {
    "skin_type": "Skin type",
    "scent": "Scent",
    "hair_type": "Hair type",
    "function": "Benefit",
    "texture": "Texture",
    "volume_ml": "Volume (ml)",
    "spf": "SPF",
    "pa": "PA",
    "flavor": "Flavor",
    "key_ingredients": "Ingredients",
}


def _priority_dimension(priority: str) -> str | None:
    value = priority.lower()
    if any(keyword in value for keyword in ("价格", "便宜", "性价比", "price", "budget")):
        return "price"
    if any(keyword in value for keyword in ("评分", "好评", "rating", "score")):
        return "rating"
    if any(keyword in value for keyword in ("口碑", "评价", "review", "reputation")):
        return "reviews"
    if any(keyword in value for keyword in ("偏好", "适合", "preference", "fit")):
        return "preference"
    if any(keyword in value for keyword in ("语义", "相关", "semantic", "relevance")):
        return "semantic"
    return None


def weights_for(priorities: list[str]) -> dict[str, float]:
    weights = dict(DEFAULT_WEIGHTS)
    for priority in priorities:
        dimension = _priority_dimension(priority)
        if dimension:
            weights[dimension] += 0.15

    total = sum(weights.values())
    return {key: round(value / total, 3) for key, value in weights.items()}


def _attribute_matches(product_value: Any, wanted: Any) -> bool:
    if isinstance(product_value, list):
        wanted_text = str(wanted).lower()
        return any(
            wanted_text in str(item).lower() or str(item).lower() in wanted_text
            for item in product_value
        )
    product_text = str(product_value).lower()
    wanted_text = str(wanted).lower()
    return wanted_text in product_text or product_text in wanted_text


def preference_score(
    product: Product, attributes: dict[str, Any]
) -> tuple[float, list[str], list[str]]:
    if not attributes:
        return 1.0, [], []

    matched: list[str] = []
    missing: list[str] = []
    for key, wanted in attributes.items():
        product_value = product.attributes.get(key)
        label = ATTRIBUTE_LABELS.get(key, key)
        if product_value is not None and _attribute_matches(product_value, wanted):
            matched.append(f"{label}: {wanted}")
        else:
            missing.append(f"{label}: {wanted}")

    score = len(matched) / (len(matched) + len(missing))
    return score, matched, missing


def _normalise(value: float, low: float, high: float) -> float:
    if high <= low:
        return 1.0
    return max(0.0, min(1.0, (value - low) / (high - low)))


def rank_products(
    products: list[Product],
    profile: ShoppingProfile,
    semantic_scores: dict[str, float] | None = None,
) -> list[ScoredProduct]:
    if not products:
        return []

    if profile.attributes:
        exact_matches = [
            product
            for product in products
            if preference_score(product, profile.attributes)[0] >= 0.999
        ]
        if len(exact_matches) >= 3:
            products = exact_matches

    prices = [product.price for product in products]
    min_price, max_price = min(prices), max(prices)
    max_reviews = max(product.review_count for product in products) or 1

    semantic_available = bool(semantic_scores)
    weights = weights_for(profile.priorities)
    if not semantic_available:
        weights.pop("semantic", None)
        total_weight = sum(weights.values())
        weights = {key: value / total_weight for key, value in weights.items()}

    scored: list[ScoredProduct] = []

    for product in products:
        price_score = 1.0 - _normalise(product.price, min_price, max_price)
        rating_score = _normalise(product.rating, 3.0, 5.0)
        review_score = math.log1p(product.review_count) / math.log1p(max_reviews)
        pref_score, matched, missing = preference_score(product, profile.attributes)
        semantic_score = (
            semantic_scores.get(product.id, 0.0) if semantic_available else 0.0
        )

        total = (
            weights["price"] * price_score
            + weights["rating"] * rating_score
            + weights["reviews"] * review_score
            + weights["preference"] * pref_score
        )
        if semantic_available:
            total += weights["semantic"] * semantic_score

        reasons: list[str] = []
        warnings: list[str] = []

        if profile.budget_max is not None:
            reasons.append(
                f"Price ¥{product.price:g}, within the ¥{profile.budget_max:g} budget"
            )
            if product.price > profile.budget_max * 0.9:
                warnings.append("Price is close to the budget limit")
        else:
            reasons.append(f"Price ¥{product.price:g}")

        reasons.append(f"Rating {product.rating:.1f}")
        if product.review_count >= 1000:
            reasons.append(
                f"{product.review_count} reviews, strong sample size"
            )
        elif product.review_count >= 100:
            reasons.append(f"{product.review_count} reviews")
        else:
            warnings.append(
                f"Limited number of reviews ({product.review_count})"
            )

        if matched:
            reasons.append("Matches preferences: " + ", ".join(matched))
        if missing:
            warnings.append("Not fully matched: " + ", ".join(missing))

        if product.rating >= 4.7:
            reasons.append("Rating is among the best in this category")
        elif product.rating < 4.3:
            warnings.append("Rating below 4.3")

        if semantic_available and semantic_score >= 0.65:
            reasons.append("High semantic relevance")

        breakdown = {
            "price": round(price_score, 3),
            "rating": round(rating_score, 3),
            "reviews": round(review_score, 3),
            "preference": round(pref_score, 3),
        }
        if semantic_available:
            breakdown["semantic"] = round(semantic_score, 3)

        scored.append(
            ScoredProduct(
                product=product,
                score=round(total, 4),
                breakdown=breakdown,
                reasons=reasons,
                warnings=warnings,
            )
        )

    scored.sort(
        key=lambda item: (item.score, item.product.rating, item.product.review_count),
        reverse=True,
    )
    return scored
