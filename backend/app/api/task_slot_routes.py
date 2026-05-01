from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.task_slot_service import TaskSlotService
from app.schemas.task_schema import (
    TaskSlotCreate,
    TaskSlotUpdate,
    TaskSlotResponse
)
from app.middleware.rate_limit import limiter, RateLimits

router = APIRouter()


@router.post(
    "/tasks/{task_id}/slots",
    response_model=TaskSlotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new slot",
    description="Create a new time slot for a specific task"
)
@limiter.limit(RateLimits.CREATE)
def create_task_slot(
    request: Request,
    task_id: int,
    slot_data: TaskSlotCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new slot for a task
    """
    service = TaskSlotService(db)
    return service.create_slot(task_id, slot_data)


@router.patch(
    "/tasks/{task_id}/slots/{slot_id}",
    response_model=TaskSlotResponse,
    summary="Update a slot",
    description="Update an existing slot (used for drag & drop or time changes)"
)
@limiter.limit(RateLimits.UPDATE)
def update_task_slot(
    request: Request,
    task_id: int,
    slot_id: int,
    slot_data: TaskSlotUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing slot
    """
    service = TaskSlotService(db)
    return service.update_slot(task_id, slot_id, slot_data)


@router.delete(
    "/tasks/{task_id}/slots/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a slot",
    description="Delete a slot (must have at least 1 slot remaining)"
)
@limiter.limit(RateLimits.DELETE)
def delete_task_slot(
    request: Request,
    task_id: int,
    slot_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a slot
    """
    service = TaskSlotService(db)
    service.delete_slot(task_id, slot_id)
    return None
