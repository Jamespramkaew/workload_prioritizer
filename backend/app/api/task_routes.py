from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.schemas.task_schema import TaskCreate, TaskUpdate, TaskResponse
from app.services.task_service import TaskService
from app.middleware.rate_limit import limiter, RateLimits

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=List[TaskResponse])
@limiter.limit(RateLimits.LIST)
def list_tasks(
    request: Request,
    week_offset: Optional[int] = Query(
        None, 
        ge=-520, 
        le=520,
        description="Filter by week offset from current week (omit = all tasks, range: -520 to 520)"
    ),
    status: str = Query(
        "active", 
        pattern="^(active|pending|in_progress|completed|cancelled|all)$",
        description="Filter by status: active, pending, in_progress, completed, cancelled, all"
    ),
    db: Session = Depends(get_db)
):
    """
    List all tasks with optional filtering
    
    Args:
        week_offset: Week offset from current week (None = all weeks)
        status: Filter by status (default: active)
        db: Database session
        
    Returns:
        List of tasks
        
    Raises:
        HTTPException 400: Invalid parameters
        HTTPException 422: Validation error
        HTTPException 500: Database error
    """
    try:
        logger.info(f"Listing tasks (week_offset={week_offset}, status={status})")
        service = TaskService(db)
        tasks = service.list_tasks(week_offset, status)
        logger.info(f"Successfully listed {len(tasks)} tasks")
        return tasks
        
    except HTTPException:
        # Re-raise HTTPExceptions from service layer
        raise
    except Exception as e:
        logger.error(f"Unexpected error in list_tasks endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tasks"
        )


@router.get("/{task_id}", response_model=TaskResponse)
@limiter.limit(RateLimits.READ)
def get_task(
    request: Request, 
    task_id: int, 
    db: Session = Depends(get_db)
):
    """
    Get a single task by ID
    
    Args:
        task_id: Task ID
        db: Database session
        
    Returns:
        Task object
        
    Raises:
        HTTPException 400: Invalid task ID
        HTTPException 404: Task not found
        HTTPException 500: Database error
    """
    try:
        logger.info(f"Getting task {task_id}")
        service = TaskService(db)
        task = service.get_task(task_id)
        
        if not task:
            logger.warning(f"Task {task_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found"
            )
        
        logger.info(f"Successfully retrieved task {task_id}")
        return task
        
    except HTTPException:
        # Re-raise HTTPExceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_task endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve task"
        )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RateLimits.CREATE)
def create_task(
    request: Request, 
    task_data: TaskCreate, 
    db: Session = Depends(get_db)
):
    """
    Create a new task
    
    Args:
        task_data: Task creation data
        db: Database session
        
    Returns:
        Created task
        
    Raises:
        HTTPException 400: Invalid data or foreign key
        HTTPException 409: Data conflict
        HTTPException 422: Validation error
        HTTPException 500: Database error
    """
    try:
        logger.info(f"Creating task: {task_data.title}")
        service = TaskService(db)
        task = service.create_task(task_data)
        logger.info(f"Successfully created task {task.id}: {task.title}")
        return task
        
    except HTTPException:
        # Re-raise HTTPExceptions from service layer
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_task endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task"
        )


@router.patch("/{task_id}", response_model=TaskResponse)
@limiter.limit(RateLimits.UPDATE)
def update_task(
    request: Request, 
    task_id: int, 
    task_data: TaskUpdate, 
    db: Session = Depends(get_db)
):
    """
    Update a task
    
    Args:
        task_id: Task ID to update
        task_data: Update data
        db: Database session
        
    Returns:
        Updated task
        
    Raises:
        HTTPException 400: Invalid data
        HTTPException 404: Task not found
        HTTPException 409: Data conflict
        HTTPException 422: Validation error
        HTTPException 500: Database error
    """
    try:
        logger.info(f"Updating task {task_id}")
        service = TaskService(db)
        task = service.update_task(task_id, task_data)
        
        if not task:
            logger.warning(f"Task {task_id} not found for update")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found"
            )
        
        logger.info(f"Successfully updated task {task_id}")
        return task
        
    except HTTPException:
        # Re-raise HTTPExceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in update_task endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task"
        )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(RateLimits.DELETE)
def delete_task(
    request: Request, 
    task_id: int, 
    db: Session = Depends(get_db)
):
    """
    Delete a task
    
    Args:
        task_id: Task ID to delete
        db: Database session
        
    Returns:
        None (204 No Content)
        
    Raises:
        HTTPException 400: Invalid task ID
        HTTPException 404: Task not found
        HTTPException 409: Data conflict
        HTTPException 500: Database error
    """
    try:
        logger.info(f"Deleting task {task_id}")
        service = TaskService(db)
        success = service.delete_task(task_id)
        
        if not success:
            logger.warning(f"Task {task_id} not found for deletion")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found"
            )
        
        logger.info(f"Successfully deleted task {task_id}")
        return None
        
    except HTTPException:
        # Re-raise HTTPExceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in delete_task endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete task"
        )
