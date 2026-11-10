from app.agent.state import ShoppingProfile
from app.models import Product
from app.services.ranking import rank_products, weights_for


def make_product(
    *,
    id: str,
    price: float,
    rating: float,
    reviews: int,
    skin_type: str = "中性",
    scent: str = "无香",
) -> Product:
    return Product(
        id=id,
        name=f"测试商品{id}",
        brand="测试",
        category="沐浴露",
        price=price,
        rating=rating,
        review_count=reviews,
        attributes={"skin_type": skin_type, "scent": scent},
        pros=[],
        cons=[],
        tags=[],
        image_key=id,
    )


def test_budget_and_preference_rank_higher():
    products = [
        make_product(
            id="cheap", price=39, rating=4.2, reviews=100, skin_type="油性", scent="花香"
        ),
        make_product(
            id="match", price=69, rating=4.7, reviews=2000, skin_type="敏感肌", scent="无香"
        ),
        make_product(
            id="premium", price=99, rating=4.8, reviews=300, skin_type="敏感肌", scent="无香"
        ),
    ]
    profile = ShoppingProfile(
        category="沐浴露",
        budget_max=100,
        attributes={"skin_type": "敏感肌", "scent": "无香"},
    )
    ranked = rank_products(products, profile)
    assert ranked[0].product.id in {"match", "premium"}
    assert ranked[0].breakdown["preference"] == 1.0
    assert all(item.product.price <= 100 for item in ranked)


def test_price_priority_changes_weights():
    default = weights_for([])
    price_first = weights_for(["价格"])
    assert price_first["price"] > default["price"]


def test_low_review_count_gets_warning():
    products = [
        make_product(id="new", price=50, rating=4.9, reviews=5),
        make_product(id="old", price=60, rating=4.5, reviews=5000),
    ]
    ranked = rank_products(products, ShoppingProfile(category="沐浴露"))
    new_item = next(item for item in ranked if item.product.id == "new")
    assert any("Limited number of reviews" in warning for warning in new_item.warnings)
