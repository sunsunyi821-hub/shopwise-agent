from datetime import UTC, datetime
from uuid import uuid4                                  

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import ChatMessage, ChatSession
from app.schemas import MessageOut, SessionOut


def get_or_create_session(
    db: Session, *, session_id: str | None, user_id: str
) -> ChatSession:                       
    if session_id:
        chat_session = db.get(ChatSession, session_id)                               
        if chat_session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        if chat_session.user_id != user_id:
            raise HTTPException(status_code=403, detail="You do not have access to this session")
        return chat_session

    chat_session = ChatSession(id=uuid4().hex, user_id=user_id)
    db.add(chat_session)                 
    db.commit()          
    db.refresh(chat_session)                
    return chat_session


def add_message(
    db: Session,
    *,
    session_id: str,
    role: str,
    content: str,
    meta: dict | None = None,                               
) -> ChatMessage:
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        meta=meta or {},                              
    )
    db.add(message)
    db.commit()    
    db.refresh(message)
    return message


def touch_session(
    db: Session,
    chat_session: ChatSession,
    profile: dict,
    title: str | None = None,
) -> None:                                  
    chat_session.profile = profile
    chat_session.updated_at = datetime.now(UTC)                             
    if title and chat_session.title == "New shopping chat":
        chat_session.title = title[:40]                                                                    
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)


def get_session_detail(db: Session, session_id: str, user_id: str) -> SessionOut:
    chat_session = db.get(ChatSession, session_id)
    if chat_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if chat_session.user_id != user_id:
        raise HTTPException(status_code=403, detail="You do not have access to this session")

    messages = list(
        db.exec(
            select(ChatMessage)             
            .where(ChatMessage.session_id == session_id)                
            .order_by(ChatMessage.id)                
        ).all()               
    )                                                 
    return SessionOut(
        id=chat_session.id,
        user_id=chat_session.user_id,
        title=chat_session.title,
        profile=chat_session.profile,
        created_at=chat_session.created_at,
        updated_at=chat_session.updated_at,
        messages=[MessageOut.model_validate(message) for message in messages],
    )


def list_sessions(db: Session, user_id: str, limit: int = 30) -> list[SessionOut]:
                         
    sessions = list(
        db.exec(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
            .limit(limit)
        ).all()
    )
    return [
        SessionOut(
            id=item.id,
            user_id=item.user_id,
            title=item.title,
            profile=item.profile,
            created_at=item.created_at,
            updated_at=item.updated_at,
            messages=[],
        )
        for item in sessions
    ]
                         
                              