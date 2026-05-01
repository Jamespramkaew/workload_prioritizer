from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.schemas.task_schema import TaskCreate, TaskUpdate, TaskResponse
from app.services.task_service import TaskService
from app.middleware.rate_limit import limiter, RateLimits

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=List[TaskResponse])
@limiter.limit(RateLimits.LIST)
def list_tasks(
    request: Request,
    week_offset: Optional[int] = Query(None, description="Filter by week (omit = all tasks)"),
    status: str = Query("active", description="Filter by status: active, pending, completed, all"),
    db: Session = Depends(get_db)
):
    return TaskService(db).list_tasks(week_offset, status)


@router.get("/{task_id}", response_model=TaskResponse)
@limiter.limit(RateLimits.READ)
def get_task(request: Request, task_id: int, db: Session = Depends(get_db)):
    task = TaskService(db).get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    return task


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RateLimits.CREATE)
def create_task(request: Request, task_data: TaskCreate, db: Session = Depends(get_db)):
    return TaskService(db).create_task(task_data)


@router.patch("/{task_id}", response_model=TaskResponse)
@limiter.limit(RateLimits.UPDATE)
def update_task(request: Request, task_id: int, task_data: TaskUpdate, db: Session = Depends(get_db)):
    task = TaskService(db).update_task(task_id, task_data)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(RateLimits.DELETE)
def delete_task(request: Request, task_id: int, db: Session = Depends(get_db)):
    success = TaskService(db).delete_task(task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    return None
