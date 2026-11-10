from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session

from app.db import get_session
from app.models import AgentTask
from app.schemas import AgentConfirmRequest, AgentRunRequest, AgentTaskOut
from app.services.agent_tasks import create_agent_task, execute_confirmed_task

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/tasks", response_model=AgentTaskOut, status_code=201)
async def run_task(
    payload: AgentRunRequest,
    request: Request,
    db: Session = Depends(get_session),
) -> AgentTaskOut:
    provider = request.app.state.provider
    embedding_provider = getattr(request.app.state, "embedding_provider", None)
    task = await create_agent_task(
        db,
        provider=provider,
        embedding_provider=embedding_provider,
        user_id=payload.user_id,
        goal=payload.goal,
    )
    return AgentTaskOut.model_validate(task)


@router.get("/tasks/{task_id}", response_model=AgentTaskOut)
def get_task(
    task_id: str,
    user_id: str = Query(default="demo-user"),
    db: Session = Depends(get_session),
) -> AgentTaskOut:
    task = db.get(AgentTask, task_id)
    if task is None or task.user_id != user_id:
        raise HTTPException(status_code=404, detail="Task not found")
    return AgentTaskOut.model_validate(task)


@router.post("/tasks/{task_id}/confirm", response_model=AgentTaskOut)
def confirm_task(
    task_id: str,
    payload: AgentConfirmRequest,
    db: Session = Depends(get_session),
) -> AgentTaskOut:
    task = db.get(AgentTask, task_id)
    if task is None or task.user_id != payload.user_id:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status == "completed":
        return AgentTaskOut.model_validate(task)
    if task.status != "awaiting_confirmation":
        raise HTTPException(status_code=400, detail="Task cannot be confirmed")
    task = execute_confirmed_task(db, task)
    return AgentTaskOut.model_validate(task)
