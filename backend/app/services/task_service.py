from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import date, timedelta
import logging

from app.models.task import Task, TaskSlot
from app.schemas.task_schema import TaskCreate, TaskUpdate

logger = logging.getLogger(__name__)


class TaskService:
    """
    Task Service with comprehensive error handling
    Manages task operations with transaction management and validation
    """
    
    def __init__(self, db: Session):
        """
        Initialize service with database session
        
        Args:
            db: SQLAlchemy database session
        """
        self._db = db

    @property
    def db(self) -> Session:
        """Get database session"""
        return self._db

    def list_tasks(
        self,
        week_offset: Optional[int] = None,
        status: str = "active"
    ) -> List[Task]:
        """
        List tasks with optional filtering
        
        Args:
            week_offset: Week offset from current week (None = all weeks)
            status: Filter by status (active, pending, in_progress, completed, cancelled, all)
            
        Returns:
            List of Task objects
            
        Raises:
            HTTPException: If database query fails
        """
        try:
            # Validate status parameter
            valid_statuses = ["active", "pending", "in_progress", "completed", "cancelled", "all"]
            if status not in valid_statuses:
                raise ValueError(
                    f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}"
                )
            
            query = self._db.query(Task)

            # Apply status filter
            if status == "active":
                query = query.filter(Task.status.in_(["pending", "in_progress"]))
            elif status != "all":
                query = query.filter(Task.status == status)

            # Apply week filter
            if week_offset is not None:
                # Validate week_offset is reasonable
                if week_offset < -520 or week_offset > 520:  # ~10 years
                    raise ValueError("Week offset must be between -520 and 520")
                
                today = date.today()
                week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
                week_end = week_start + timedelta(days=6)
                query = query.filter(
                    Task.deadline_date >= week_start, 
                    Task.deadline_date <= week_end
                )

            tasks = query.order_by(Task.deadline_date, Task.importance.desc()).all()
            logger.info(f"Listed {len(tasks)} tasks (status={status}, week_offset={week_offset})")
            return tasks
            
        except ValueError as e:
            logger.warning(f"Validation error listing tasks: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error listing tasks: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve tasks"
            )
        except Exception as e:
            logger.error(f"Unexpected error listing tasks: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    def get_task(self, task_id: int) -> Optional[Task]:
        """
        Get a single task by ID
        
        Args:
            task_id: Task ID
            
        Returns:
            Task object or None if not found
            
        Raises:
            HTTPException: If database query fails
        """
        try:
            # Validate task_id
            if task_id <= 0:
                raise ValueError("Task ID must be positive")
            
            task = self._db.query(Task).filter(Task.id == task_id).first()
            
            if task:
                logger.info(f"Retrieved task {task_id}: {task.title}")
            else:
                logger.info(f"Task {task_id} not found")
            
            return task
            
        except ValueError as e:
            logger.warning(f"Validation error getting task: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error getting task {task_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve task"
            )
        except Exception as e:
            logger.error(f"Unexpected error getting task {task_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    def create_task(self, task_data: TaskCreate) -> Task:
        """
        Create a new task with transaction management
        
        Args:
            task_data: Task creation data
            
        Returns:
            Created Task object
            
        Raises:
            HTTPException: If creation fails
        """
        try:
            # Additional validation
            if task_data.user_id and task_data.user_id <= 0:
                raise ValueError("User ID must be positive")
            
            if task_data.subject_id and task_data.subject_id <= 0:
                raise ValueError("Subject ID must be positive")
            
            if not task_data.title or not task_data.title.strip():
                raise ValueError("Task title is required")
            
            if task_data.estimated_hours <= 0:
                raise ValueError("Estimated hours must be positive")
            
            # Validate deadline is not too far in past
            if task_data.deadline_date < date.today() - timedelta(days=365):
                raise ValueError("Deadline cannot be more than 1 year in the past")
            
            # Create task
            task = Task(
                user_id=task_data.user_id,
                subject_id=task_data.subject_id,
                title=task_data.title,
                deadline_date=task_data.deadline_date,
                difficulty=task_data.difficulty,
                importance=task_data.importance,
                comfortable=task_data.comfortable,
                estimated_hours=task_data.estimated_hours,
                status=task_data.status
            )
            self._db.add(task)
            self._db.flush()

            # Create task slots if provided
            if task_data.slots:
                total_slot_hours = 0
                for slot_data in task_data.slots:
                    # Validate slot data
                    if slot_data.hours <= 0:
                        raise ValueError("Slot hours must be positive")
                    
                    if slot_data.start_hour < 0 or slot_data.start_hour >= 24:
                        raise ValueError("Slot start hour must be between 0 and 24")
                    
                    if slot_data.start_hour + slot_data.hours > 24:
                        raise ValueError(
                            f"Slot time exceeds 24 hours: "
                            f"{slot_data.start_hour} + {slot_data.hours} = "
                            f"{slot_data.start_hour + slot_data.hours}"
                        )
                    
                    total_slot_hours += slot_data.hours
                    
                    slot = TaskSlot(
                        task_id=task.id,
                        slot_date=slot_data.slot_date,
                        start_hour=slot_data.start_hour,
                        hours=slot_data.hours
                    )
                    self._db.add(slot)
                
                # Validate total slot hours don't exceed estimated hours
                if total_slot_hours > task_data.estimated_hours:
                    raise ValueError(
                        f"Total slot hours ({total_slot_hours}) cannot exceed "
                        f"estimated hours ({task_data.estimated_hours})"
                    )

            self._db.commit()
            self._db.refresh(task)
            
            logger.info(
                f"Created task {task.id}: {task.title} "
                f"(deadline: {task.deadline_date}, slots: {len(task_data.slots or [])})"
            )
            return task
            
        except ValueError as e:
            self._db.rollback()
            logger.warning(f"Validation error creating task: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Integrity error creating task: {str(e)}")
            
            # Check for specific constraint violations
            error_msg = str(e.orig).lower()
            if 'foreign key' in error_msg:
                if 'user_id' in error_msg:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid user ID"
                    )
                elif 'subject_id' in error_msg:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid subject ID"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid foreign key reference"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Task creation failed due to data conflict"
                )
        except SQLAlchemyError as e:
            self._db.rollback()
            logger.error(f"Database error creating task: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create task"
            )
        except Exception as e:
            self._db.rollback()
            logger.error(f"Unexpected error creating task: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    def update_task(self, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
        """
        Update a task with transaction management
        
        Args:
            task_id: Task ID to update
            task_data: Update data
            
        Returns:
            Updated Task object or None if not found
            
        Raises:
            HTTPException: If update fails
        """
        try:
            # Validate task_id
            if task_id <= 0:
                raise ValueError("Task ID must be positive")
            
            # Get existing task
            task = self._db.query(Task).filter(Task.id == task_id).first()
            if not task:
                logger.info(f"Task {task_id} not found for update")
                return None
            
            # Validate updates
            if task_data.title is not None:
                if not task_data.title.strip():
                    raise ValueError("Task title cannot be empty")
            
            if task_data.status is not None:
                valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
                if task_data.status not in valid_statuses:
                    raise ValueError(
                        f"Invalid status '{task_data.status}'. "
                        f"Must be one of: {', '.join(valid_statuses)}"
                    )
            
            # Update fields
            if task_data.title is not None:
                task.title = task_data.title
            if task_data.status is not None:
                task.status = task_data.status

            self._db.commit()
            self._db.refresh(task)
            
            logger.info(f"Updated task {task_id}: {task.title}")
            return task
            
        except ValueError as e:
            self._db.rollback()
            logger.warning(f"Validation error updating task {task_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Integrity error updating task {task_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Task update failed due to data conflict"
            )
        except SQLAlchemyError as e:
            self._db.rollback()
            logger.error(f"Database error updating task {task_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update task"
            )
        except Exception as e:
            self._db.rollback()
            logger.error(f"Unexpected error updating task {task_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    def delete_task(self, task_id: int) -> bool:
        """
        Delete a task with transaction management
        
        Args:
            task_id: Task ID to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            HTTPException: If deletion fails
        """
        try:
            # Validate task_id
            if task_id <= 0:
                raise ValueError("Task ID must be positive")
            
            task = self._db.query(Task).filter(Task.id == task_id).first()
            if not task:
                logger.info(f"Task {task_id} not found for deletion")
                return False

            task_title = task.title
            slot_count = len(task.task_slots) if hasattr(task, 'task_slots') else 0
            
            # Delete task (cascade will delete slots automatically)
            self._db.delete(task)
            self._db.commit()
            
            logger.info(
                f"Deleted task {task_id}: {task_title} "
                f"(with {slot_count} slots)"
            )
            return True
            
        except ValueError as e:
            self._db.rollback()
            logger.warning(f"Validation error deleting task {task_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Integrity error deleting task {task_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Task deletion failed due to data conflict"
            )
        except SQLAlchemyError as e:
            self._db.rollback()
            logger.error(f"Database error deleting task {task_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete task"
            )
        except Exception as e:
            self._db.rollback()
            logger.error(f"Unexpected error deleting task {task_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )
