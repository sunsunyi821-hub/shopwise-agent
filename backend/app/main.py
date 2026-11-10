import logging
from contextlib import asynccontextmanager


















from fastapi import FastAPI















from fastapi.middleware.cors import CORSMiddleware





















from sqlmodel import Session







from app.agent.embeddings import create_embedding_provider
from app.agent.llm import create_provider
from app.api import (
    routes_agent,
    routes_chat,
    routes_health,
    routes_orders,
    routes_products,
    routes_reviews,
    routes_seller,
    routes_sessions,
)

from app.config import get_settings
from app.db import engine, init_db



from app.seed import seed_if_empty



from app.services.semantic import ensure_embeddings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)



settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with Session(engine) as session:
        seeded = seed_if_empty(session)












        if seeded:
            logger.info("Demo catalog seeded")

    app.state.provider = create_provider(settings)






    logger.info("LLM provider: %s", getattr(app.state.provider, "name", "unknown"))

    embedding_provider = create_embedding_provider(settings)
    if embedding_provider is not None:
        try:
            with Session(engine) as session:













                refreshed = await ensure_embeddings(session, embedding_provider)
            logger.info(
                "Embedding provider: %s (%s products refreshed)",
                embedding_provider.model,
                refreshed,
            )
        except Exception as exc:
            logger.warning("Semantic retrieval disabled at startup: %s", exc)
            embedding_provider = None
    else:
        logger.info(
            "Semantic retrieval disabled (EMBEDDING_PROVIDER=%s)",
            settings.embedding_provider,
        )
    app.state.embedding_provider = embedding_provider
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="ShopWise shopping decision agent API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_health.router, prefix="/api")
app.include_router(routes_products.router, prefix="/api")
app.include_router(routes_chat.router, prefix="/api")
app.include_router(routes_orders.router, prefix="/api")
app.include_router(routes_reviews.router, prefix="/api")
app.include_router(routes_seller.router, prefix="/api")
app.include_router(routes_sessions.router, prefix="/api")
app.include_router(routes_agent.router, prefix="/api")


@app.get("/")







def root() -> dict:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/health",
    }


















































