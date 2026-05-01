from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.services.task_slot_service import TaskSlotService
from app.schemas.task_schema import (
    TaskSlotCreate,
    TaskSlotUpdate,
    TaskSlotResponse
)
from app.middleware.rate_limit import limiter, RateLimits

logger = logging.getLogger(__name__)

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
    Create a new time slot for a task
    
    Args:
        task_id: Task ID
        slot_data: Slot creation data
        db: Database session
        
    Returns:
        Created slot
        
    Raises:
        HTTPException 400: Invalid data or validation error
        HTTPException 404: Task not found
        HTTPException 409: Data conflict
        HTTPException 422: Validation error
        HTTPException 500: Database error
    """
    try:
        logger.info(f"Creating slot for task {task_id}: {slot_data.slot_date} {slot_data.start_hour}h")
        service = TaskSlotService(db)
        slot = service.create_slot(task_id, slot_data)
        logger.info(f"Successfully created slot {slot.id} for task {task_id}")
        return slot
        
    except HTTPException:
        # Re-raise HTTPExceptions from service layer
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_task_slot endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create slot"
        )


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
    Update an existing time slot
    
    Args:
        task_id: Task ID
        slot_id: Slot ID to update
        slot_data: Update data
        db: Database session
        
    Returns:
        Updated slot
        
    Raises:
        HTTPException 400: Invalid data or validation error
        HTTPException 404: Slot not found
        HTTPException 409: Data conflict
        HTTPException 422: Validation error
        HTTPException 500: Database error
    """
    try:
        logger.info(f"Updating slot {slot_id} for task {task_id}")
        service = TaskSlotService(db)
        slot = service.update_slot(task_id, slot_id, slot_data)
        logger.info(f"Successfully updated slot {slot_id} for task {task_id}")
        return slot
        
    except HTTPException:
        # Re-raise HTTPExceptions from service layer
        raise
    except Exception as e:
        logger.error(f"Unexpected error in update_task_slot endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update slot"
        )


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
    Delete a time slot
    
    Args:
        task_id: Task ID
        slot_id: Slot ID to delete
        db: Database session
        
    Returns:
        None (204 No Content)
        
    Raises:
        HTTPException 400: Invalid ID or cannot delete last slot
        HTTPException 404: Slot not found
        HTTPException 409: Data conflict
        HTTPException 500: Database error
    """
    try:
        logger.info(f"Deleting slot {slot_id} for task {task_id}")
        service = TaskSlotService(db)
        service.delete_slot(task_id, slot_id)
        logger.info(f"Successfully deleted slot {slot_id} for task {task_id}")
        return None
        
    except HTTPException:
        # Re-raise HTTPExceptions from service layer
        raise
    except Exception as e:
        logger.error(f"Unexpected error in delete_task_slot endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete slot"
        )
