import logging
from datetime import UTC, datetime
from uuid import uuid4

from sqlmodel import Session

from app.agent.embeddings import EmbeddingProvider
from app.agent.llm import LLMProvider
from app.agent.mock import MockProvider
from app.agent.orchestrator import run_shopping_agent
from app.agent.state import ScoredProduct, SellerProductDraft, ShoppingProfile
from app.models import AgentTask, Order
from app.schemas import OrderOut, ProductOut, ScoredProductOut
from app.services.agent_policy import PlanValidationError, normalize_plan
from app.services.catalog import get_product, list_categories
from app.services.seller import analyze_seller_product, create_seller_product

logger = logging.getLogger(__name__)

DEFAULT_ADDRESS = "1 Demo Road, Shanghai"


def _scored_payload(item: ScoredProduct) -> dict:
    return ScoredProductOut(
        product=ProductOut.model_validate(item.product),
        score=item.score,
        breakdown=item.breakdown,
        reasons=item.reasons,
        warnings=item.warnings,
    ).model_dump(mode="json")


def _append_result(task: AgentTask, payload: dict) -> None:
    task.results = [*task.results, payload]
    task.updated_at = datetime.now(UTC)


def _fail(task: AgentTask, message: str) -> None:
    task.status = "failed"
    _append_result(task, {"skill": "error", "message": message})


def _order_draft(
    item: ScoredProduct,
    args: dict,
    address: str,
) -> dict:
    product = item.product
    quantity = int(args.get("quantity") or 1)
    return {
        "skill": "order",
        "product_id": product.id,
        "product_name": product.name,
        "brand": product.brand,
        "unit_price": product.price,
        "quantity": quantity,
        "total": round(product.price * quantity, 2),
        "address": address,
        "max_price": args.get("max_price"),
    }


def _create_order(db: Session, task: AgentTask, draft: dict) -> Order:
    product = get_product(db, str(draft["product_id"]))
    if product is None:
        raise ValueError("Product not found")
    unit_price = float(draft["unit_price"])
    if abs(product.price - unit_price) > 0.01:
        raise ValueError("Product price changed; please replan")
    quantity = int(draft["quantity"])
    order = Order(
        id=f"SW-{datetime.now(UTC):%Y%m%d}-{uuid4().hex[:6].upper()}",
        user_id=task.user_id,
        session_id=None,
        product_id=product.id,
        product_name=product.name,
        quantity=quantity,
        unit_price=product.price,
        total_price=round(product.price * quantity, 2),
        status="confirmed",
        address=str(draft["address"]),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


async def _enrich_sell_args(
    goal: str,
    args: dict,
    valid_categories: set[str],
) -> dict:
    """Fill missing or invalid seller fields from the original goal with rules."""
    category = str(args.get("category") or "").strip()
    price = args.get("price")
    if category in valid_categories and price is not None:
        return args

    fallback = await MockProvider().plan_tasks(goal)
    for step in fallback.steps:
        if step.skill != "sell":
            continue
        merged = dict(args)
        merged.update(
            {
                key: value
                for key, value in step.args.items()
                if value not in (None, "")
            }
        )
        return merged
    return args


async def create_agent_task(
    db: Session,
    *,
    provider: LLMProvider,
    embedding_provider: EmbeddingProvider | None,
    user_id: str,
    goal: str,
) -> AgentTask:
    """Plan a task and execute until the first step that needs confirmation."""
    degraded = False
    try:
        plan = await provider.plan_tasks(goal)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Task planning failed (%s), falling back to rules: %s",
            provider.name,
            exc,
        )
        plan = await MockProvider().plan_tasks(goal)
        degraded = True

    try:
        plan = normalize_plan(plan, goal)
    except PlanValidationError as exc:
        task = AgentTask(
            id=uuid4().hex,
            user_id=user_id,
            goal=goal,
            status="failed",
            risk="read",
            plan=plan.model_dump(),
            results=[{"skill": "error", "message": str(exc)}],
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    task = AgentTask(
        id=uuid4().hex,
        user_id=user_id,
        goal=goal,
        status="planned",
        risk="read",
        plan=plan.model_dump(),
        results=[],
    )
    if degraded:
        _append_result(
            task,
            {
                "skill": "planner",
                "message": "LLM planning failed; using a rule-based plan",
            },
        )
    db.add(task)
    db.commit()
    db.refresh(task)

    top_item: ScoredProduct | None = None

    for step in plan.steps:
        task.risk = step.risk
        if step.skill == "recommend":
            result = await run_shopping_agent(
                session=db,
                provider=provider,
                message=goal,
                profile=ShoppingProfile(),
                embedding_provider=embedding_provider,
            )
            if result.scored:
                top = result.scored[0].product
                summary = (
                    f"Found {len(result.scored)} candidates. "
                    f"Top pick: {top.name} (¥{top.price:g})"
                )
            else:
                summary = result.clarification or "No matching products found."
            _append_result(
                task,
                {
                    "skill": "recommend",
                    "summary": summary,
                    "top_product_id": result.top_product_id,
                    "products": [_scored_payload(item) for item in result.scored],
                    "relaxations": result.relaxations,
                },
            )
            if result.scored:
                top_item = result.scored[0]
            if result.clarification or not result.scored:
                task.status = "needs_input"
                task.risk = "read"
                db.add(task)
                db.commit()
                db.refresh(task)
                return task

        elif step.skill == "order":
            if top_item is None:
                _fail(task, "No product is available for ordering")
                db.add(task)
                db.commit()
                db.refresh(task)
                return task
            max_price = step.args.get("max_price")
            if max_price is not None and top_item.product.price > float(max_price):
                _fail(task, "The recommended product exceeds the price limit")
                db.add(task)
                db.commit()
                db.refresh(task)
                return task
            task.draft = _order_draft(top_item, step.args, DEFAULT_ADDRESS)
            task.status = "awaiting_confirmation"
            task.risk = "write"
            db.add(task)
            db.commit()
            db.refresh(task)
            return task

        elif step.skill == "sell":
            valid_categories = set(list_categories(db))
            sell_args = await _enrich_sell_args(
                goal, step.args, valid_categories
            )
            category = str(sell_args.get("category") or "").strip()
            price = sell_args.get("price")
            if not category or category not in valid_categories:
                _fail(
                    task,
                    "Please specify a product category, for example: 洗发水, 面霜, 沐浴露",
                )
                db.add(task)
                db.commit()
                db.refresh(task)
                return task
            if price is None:
                _fail(task, "Please specify a listing price")
                db.add(task)
                db.commit()
                db.refresh(task)
                return task

            draft, seller_degraded = await analyze_seller_product(
                provider,
                str(sell_args.get("description") or goal),
                category,
                float(price),
                sell_args.get("brand"),
            )
            task.draft = {
                "skill": "sell",
                "draft": draft.model_dump(),
                "category": category,
                "price": float(price),
                "seller_id": user_id,
                "description": str(sell_args.get("description") or goal),
                "degraded": seller_degraded,
            }
            task.status = "awaiting_confirmation"
            task.risk = "write"
            db.add(task)
            db.commit()
            db.refresh(task)
            return task

        elif step.skill == "flash_sale":
            if top_item is None:
                _fail(task, "No product is available for the flash purchase")
                db.add(task)
                db.commit()
                db.refresh(task)
                return task
            max_price = step.args.get("max_price")
            if max_price is not None and top_item.product.price > float(max_price):
                _fail(task, "The product price exceeds the flash-sale limit")
                db.add(task)
                db.commit()
                db.refresh(task)
                return task
            quantity = int(step.args.get("quantity") or 1)
            task.draft = {
                "skill": "flash_sale",
                "product_id": top_item.product.id,
                "product_name": top_item.product.name,
                "brand": top_item.product.brand,
                "unit_price": top_item.product.price,
                "quantity": quantity,
                "total": round(top_item.product.price * quantity, 2),
                "max_price": max_price,
                "max_quantity": quantity,
                "address": DEFAULT_ADDRESS,
                "note": "Simulated flash purchase; no real platform or payment",
            }
            task.status = "awaiting_confirmation"
            task.risk = "high_risk"
            db.add(task)
            db.commit()
            db.refresh(task)
            return task

    task.status = "completed"
    task.risk = "read"
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def execute_confirmed_task(db: Session, task: AgentTask) -> AgentTask:
    """Execute a confirmed write step. The caller validates ownership/status."""
    if task.status != "awaiting_confirmation":
        return task
    draft = task.draft or {}
    skill = draft.get("skill")

    try:
        if skill == "order":
            order = _create_order(db, task, draft)
            _append_result(
                task,
                {
                    "skill": "order",
                    "status": "completed",
                    "order": OrderOut.model_validate(order).model_dump(mode="json"),
                },
            )
        elif skill == "flash_sale":
            product = get_product(db, str(draft["product_id"]))
            if product is None:
                raise ValueError("Product not found")
            max_price = draft.get("max_price")
            if max_price is not None and product.price > float(max_price):
                raise ValueError("Product price exceeds the flash-sale limit")
            if int(draft["quantity"]) > int(draft.get("max_quantity") or 1):
                raise ValueError("Quantity exceeds the pre-authorized limit")
            order = _create_order(db, task, draft)
            _append_result(
                task,
                {
                    "skill": "flash_sale",
                    "status": "completed",
                    "note": "Simulated flash purchase succeeded; no real platform or payment",
                    "order": OrderOut.model_validate(order).model_dump(mode="json"),
                },
            )
        elif skill == "sell":
            product_draft = SellerProductDraft.model_validate(draft["draft"])
            product = create_seller_product(
                db,
                draft=product_draft,
                category=str(draft["category"]),
                price=float(draft["price"]),
                seller_id=task.user_id,
                description=str(draft["description"]),
            )
            _append_result(
                task,
                {
                    "skill": "sell",
                    "status": "completed",
                    "product": ProductOut.model_validate(product).model_dump(mode="json"),
                },
            )
        else:
            raise ValueError("No executable draft")

        task.status = "completed"
        task.updated_at = datetime.now(UTC)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    except Exception as exc:  # noqa: BLE001
        logger.warning("Confirmed task execution failed: %s", exc)
        _fail(task, str(exc))
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
