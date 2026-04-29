from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.task_slot_service import TaskSlotService
from app.schemas.task_schema import (
    TaskSlotCreate,
    TaskSlotUpdate,
    TaskSlotResponse
)

router = APIRouter()


@router.post(
    "/tasks/{task_id}/slots",
    response_model=TaskSlotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new slot",
    description="Create a new time slot for a specific task"
)
def create_task_slot(
    task_id: int,
    slot_data: TaskSlotCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new slot for a task
    
    - **task_id**: ID of the parent task
    - **slot_date**: Date of the slot (YYYY-MM-DD)
    - **start_hour**: Start hour (0-23.99)
    - **hours**: Duration in hours (0.5-12)
    """
    service = TaskSlotService(db)
    return service.create_slot(task_id, slot_data)


@router.patch(
    "/tasks/{task_id}/slots/{slot_id}",
    response_model=TaskSlotResponse,
    summary="Update a slot",
    description="Update an existing slot (used for drag & drop or time changes)"
)
def update_task_slot(
    task_id: int,
    slot_id: int,
    slot_data: TaskSlotUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing slot
    
    - **task_id**: ID of the parent task
    - **slot_id**: ID of the slot to update
    - **slot_date**: (Optional) New date for the slot
    - **start_hour**: (Optional) New start hour
    - **hours**: (Optional) New duration
    
    Use cases:
    - Drag & drop: Update only slot_date
    - Change time: Update start_hour
    - Change duration: Update hours
    """
    service = TaskSlotService(db)
    return service.update_slot(task_id, slot_id, slot_data)


@router.delete(
    "/tasks/{task_id}/slots/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a slot",
    description="Delete a slot (must have at least 1 slot remaining)"
)
def delete_task_slot(
    task_id: int,
    slot_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a slot
    
    - **task_id**: ID of the parent task
    - **slot_id**: ID of the slot to delete
    
    Note: Cannot delete the last slot. A task must have at least one slot.
    """
    service = TaskSlotService(db)
    service.delete_slot(task_id, slot_id)
    return None
