from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request) -> dict:
    provider = getattr(request.app.state, "provider", None)
    embedding = getattr(request.app.state, "embedding_provider", None)
    return {
        "status": "ok",
        "service": "shopwise-api",
        "provider": getattr(provider, "name", "unknown"),
        "semantic": getattr(embedding, "model", None) or "disabled",
    }
