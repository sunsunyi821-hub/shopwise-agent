from dataclasses import dataclass, field

from sqlmodel import Session, select

from app.agent.state import ShoppingProfile
from app.models import Product


@dataclass
class SearchResult:
    products: list[Product] = field(default_factory=list)
    relaxations: list[str] = field(default_factory=list)


def _text_blob(product: Product) -> str:
    parts = [
        product.name,
        product.brand,
        product.category,
        product.description,
        *product.tags,
                                 
        *[str(value) for value in product.attributes.values()],
    ]
    return " ".join(parts).lower()
               

def _passes_exclusions(product: Product, exclude_keywords: list[str]) -> bool:
    blob = _text_blob(product)
    return not any(keyword.lower() in blob for keyword in exclude_keywords if keyword)
                       

def _matches_include_brands(product: Product, brands: list[str]) -> bool:
    if not brands:
        return True
    return product.brand in brands


def _query_matches(product: Product, query: str | None) -> bool:
    if not query:
        return True
    return query.lower() in _text_blob(product)


def search_for_profile(session: Session, profile: ShoppingProfile) -> SearchResult:
    """Search the catalog for a shopping profile, relaxing constraints if needed."""
    relaxations: list[str] = []

    def run(
        *,
        category: str | None,
        budget_max: float | None,
        min_rating: float | None,
    ) -> list[Product]:
        statement = select(Product)
        if category:
            statement = statement.where(Product.category == category)
        if budget_max is not None:
            statement = statement.where(Product.price <= budget_max)
        if min_rating is not None:
            statement = statement.where(Product.rating >= min_rating)
        if profile.brands_exclude:
            statement = statement.where(Product.brand.notin_(profile.brands_exclude))
        return list(session.exec(statement).all())

    products = run(
        category=profile.category,
        budget_max=profile.budget_max,
        min_rating=profile.min_rating,
    )
    products = [
        p
        for p in products
        if _passes_exclusions(p, profile.exclude_keywords)
        and _matches_include_brands(p, profile.brands_include)
        and _query_matches(p, profile.query)
    ]

    if not products and profile.min_rating is not None:
        relaxations.append(
            f"Minimum rating constraint ({profile.min_rating}) was removed"
        )
        products = run(
            category=profile.category,
            budget_max=profile.budget_max,
            min_rating=None,
        )
        products = [
            p
            for p in products
            if _passes_exclusions(p, profile.exclude_keywords)
            and _matches_include_brands(p, profile.brands_include)
            and _query_matches(p, profile.query)
        ]

    if not products and profile.budget_max is not None:
        relaxed_budget = round(profile.budget_max * 1.2, 2)
        relaxations.append(
            f"Budget expanded from ¥{profile.budget_max:g} to ¥{relaxed_budget:g}"
        )
        products = run(
            category=profile.category,
            budget_max=relaxed_budget,
            min_rating=None,
        )
        products = [
            p
            for p in products
            if _passes_exclusions(p, profile.exclude_keywords)
            and _matches_include_brands(p, profile.brands_include)
            and _query_matches(p, profile.query)
        ]

    if not products and profile.category:
        relaxations.append(
            "All filters were relaxed; showing popular products in this category"
        )
        products = run(category=profile.category, budget_max=None, min_rating=None)
        products = [
            p
            for p in products
            if _passes_exclusions(p, profile.exclude_keywords)
            and _matches_include_brands(p, profile.brands_include)
        ]
        products.sort(key=lambda p: (p.rating, p.review_count), reverse=True)

    return SearchResult(products=products, relaxations=relaxations)


def list_catalog(
    session: Session,
    *,
    category: str | None = None,
    max_price: float | None = None,
    min_rating: float | None = None,
    q: str | None = None,
    limit: int = 50,
) -> list[Product]:
    statement = select(Product)
    if category:
        statement = statement.where(Product.category == category)
    if max_price is not None:
        statement = statement.where(Product.price <= max_price)
    if min_rating is not None:
        statement = statement.where(Product.rating >= min_rating)

    products = list(session.exec(statement).all())
    if q:
        products = [p for p in products if q.lower() in _text_blob(p)]
    products.sort(key=lambda p: (p.rating, p.review_count), reverse=True)
    return products[:limit]


def get_product(session: Session, product_id: str) -> Product | None:
    return session.get(Product, product_id)


def list_categories(session: Session) -> list[str]:
    products = list(session.exec(select(Product)).all())
    return sorted({product.category for product in products})
