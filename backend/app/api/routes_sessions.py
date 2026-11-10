from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.db import get_session
from app.schemas import SessionOut
from app.services.sessions import get_session_detail, list_sessions

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionOut])
def sessions(
    user_id: str = Query(default="demo-user"),
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_session),
) -> list[SessionOut]:
    return list_sessions(db, user_id=user_id, limit=limit)


@router.get("/{session_id}", response_model=SessionOut)
def session_detail(
    session_id: str,
    user_id: str = Query(default="demo-user"),
    db: Session = Depends(get_session),
) -> SessionOut:
    return get_session_detail(db, session_id=session_id, user_id=user_id)
                                                                       
                                                              