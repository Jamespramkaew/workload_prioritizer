from typing import List, Optional
import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.task_schema import TaskCreate, TaskUpdate, TaskResponse
from app.services.task_service import TaskService

logger = logging.getLogger(__name__)


class TaskController:
    """
    Task Controller with comprehensive error handling
    Acts as an intermediary between routes and service layer
    """
    
    def __init__(self, db: Session):
        """
        Initialize controller with database session
        
        Args:
            db: SQLAlchemy database session
        """
        self._service = TaskService(db)

    def list_tasks(self, week_offset: Optional[int], status: str) -> List[TaskResponse]:
        """
        List tasks with optional filtering
        
        Args:
            week_offset: Week offset from current week
            status: Filter by status
            
        Returns:
            List of tasks
            
        Raises:
            HTTPException: If service layer raises an error
        """
        try:
            logger.info(f"Controller: Listing tasks (week_offset={week_offset}, status={status})")
            tasks = self._service.list_tasks(week_offset, status)
            logger.info(f"Controller: Successfully listed {len(tasks)} tasks")
            return tasks
        except HTTPException:
            # Re-raise HTTPExceptions from service layer
            raise
        except Exception as e:
            logger.error(f"Controller: Unexpected error listing tasks: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve tasks"
            )

    def get_task(self, task_id: int) -> TaskResponse:
        """
        Get a single task by ID
        
        Args:
            task_id: Task ID
            
        Returns:
            Task object
            
        Raises:
            HTTPException: If task not found or service error
        """
        try:
            logger.info(f"Controller: Getting task {task_id}")
            task = self._service.get_task(task_id)
            
            if not task:
                logger.warning(f"Controller: Task {task_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task with id {task_id} not found"
                )
            
            logger.info(f"Controller: Successfully retrieved task {task_id}")
            return task
        except HTTPException:
            # Re-raise HTTPExceptions
            raise
        except Exception as e:
            logger.error(f"Controller: Unexpected error getting task {task_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve task"
            )

    def create_task(self, task_data: TaskCreate) -> TaskResponse:
        """
        Create a new task
        
        Args:
            task_data: Task creation data
            
        Returns:
            Created task
            
        Raises:
            HTTPException: If creation fails
        """
        try:
            logger.info(f"Controller: Creating task: {task_data.title}")
            task = self._service.create_task(task_data)
            logger.info(f"Controller: Successfully created task {task.id}")
            return task
        except HTTPException:
            # Re-raise HTTPExceptions from service layer
            raise
        except Exception as e:
            logger.error(f"Controller: Unexpected error creating task: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create task"
            )

    def update_task(self, task_id: int, task_data: TaskUpdate) -> TaskResponse:
        """
        Update a task
        
        Args:
            task_id: Task ID to update
            task_data: Update data
            
        Returns:
            Updated task
            
        Raises:
            HTTPException: If task not found or update fails
        """
        try:
            logger.info(f"Controller: Updating task {task_id}")
            task = self._service.update_task(task_id, task_data)
            
            if not task:
                logger.warning(f"Controller: Task {task_id} not found for update")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task with id {task_id} not found"
                )
            
            logger.info(f"Controller: Successfully updated task {task_id}")
            return task
        except HTTPException:
            # Re-raise HTTPExceptions
            raise
        except Exception as e:
            logger.error(f"Controller: Unexpected error updating task {task_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update task"
            )

    def delete_task(self, task_id: int) -> None:
        """
        Delete a task
        
        Args:
            task_id: Task ID to delete
            
        Raises:
            HTTPException: If task not found or deletion fails
        """
        try:
            logger.info(f"Controller: Deleting task {task_id}")
            success = self._service.delete_task(task_id)
            
            if not success:
                logger.warning(f"Controller: Task {task_id} not found for deletion")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task with id {task_id} not found"
                )
            
            logger.info(f"Controller: Successfully deleted task {task_id}")
        except HTTPException:
            # Re-raise HTTPExceptions
            raise
        except Exception as e:
            logger.error(f"Controller: Unexpected error deleting task {task_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete task"
            )
