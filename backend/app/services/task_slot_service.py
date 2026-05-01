from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from fastapi import HTTPException, status
from typing import List, Optional
import logging

from app.models.task import Task, TaskSlot
from app.schemas.task_schema import TaskSlotCreate, TaskSlotUpdate

logger = logging.getLogger(__name__)


class TaskSlotService:
    """
    Task Slot Service with comprehensive error handling
    Manages task slot operations with transaction management and validation
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

    def create_slot(self, task_id: int, slot_data: TaskSlotCreate) -> TaskSlot:
        """
        Create a new time slot for a task
        
        Args:
            task_id: Task ID
            slot_data: Slot creation data
            
        Returns:
            Created TaskSlot object
            
        Raises:
            HTTPException: If creation fails
        """
        try:
            # Validate task_id
            if task_id <= 0:
                raise ValueError("Task ID must be positive")
            
            # Check if task exists
            task = self._db.query(Task).filter(Task.id == task_id).first()
            if not task:
                logger.warning(f"Task {task_id} not found for slot creation")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task with id {task_id} not found"
                )
            
            # Additional validation
            if slot_data.hours <= 0:
                raise ValueError("Slot hours must be positive")
            
            if slot_data.start_hour < 0 or slot_data.start_hour >= 24:
                raise ValueError("Start hour must be between 0 and 24")
            
            if slot_data.start_hour + slot_data.hours > 24:
                raise ValueError(
                    f"Slot time exceeds 24 hours: "
                    f"{slot_data.start_hour} + {slot_data.hours} = "
                    f"{slot_data.start_hour + slot_data.hours}"
                )
            
            # Check if total slot hours would exceed estimated hours
            existing_slots = self._db.query(TaskSlot).filter(
                TaskSlot.task_id == task_id
            ).all()
            total_existing_hours = sum(float(slot.hours) for slot in existing_slots if slot.hours)
            new_total_hours = total_existing_hours + slot_data.hours
            
            if task.estimated_hours and new_total_hours > float(task.estimated_hours):
                logger.warning(
                    f"Total slot hours ({new_total_hours}) would exceed "
                    f"estimated hours ({task.estimated_hours}) for task {task_id}"
                )
                raise ValueError(
                    f"Total slot hours ({new_total_hours:.1f}) would exceed "
                    f"estimated hours ({float(task.estimated_hours):.1f})"
                )
            
            # Create slot
            new_slot = TaskSlot(
                task_id=task_id,
                slot_date=slot_data.slot_date,
                start_hour=slot_data.start_hour,
                hours=slot_data.hours
            )
            self._db.add(new_slot)
            self._db.commit()
            self._db.refresh(new_slot)
            
            logger.info(
                f"Created slot {new_slot.id} for task {task_id}: "
                f"{slot_data.slot_date} {slot_data.start_hour}-"
                f"{slot_data.start_hour + slot_data.hours} ({slot_data.hours}h)"
            )
            return new_slot
            
        except ValueError as e:
            self._db.rollback()
            logger.warning(f"Validation error creating slot for task {task_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            # Re-raise HTTPExceptions
            raise
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Integrity error creating slot for task {task_id}: {str(e)}")
            
            error_msg = str(e.orig).lower()
            if 'foreign key' in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid task ID: {task_id}"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Slot creation failed due to data conflict"
                )
        except SQLAlchemyError as e:
            self._db.rollback()
            logger.error(f"Database error creating slot for task {task_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create slot"
            )
        except Exception as e:
            self._db.rollback()
            logger.error(f"Unexpected error creating slot for task {task_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    def update_slot(self, task_id: int, slot_id: int, slot_data: TaskSlotUpdate) -> TaskSlot:
        """
        Update an existing time slot
        
        Args:
            task_id: Task ID
            slot_id: Slot ID to update
            slot_data: Update data
            
        Returns:
            Updated TaskSlot object
            
        Raises:
            HTTPException: If update fails
        """
        try:
            # Validate IDs
            if task_id <= 0:
                raise ValueError("Task ID must be positive")
            
            if slot_id <= 0:
                raise ValueError("Slot ID must be positive")
            
            # Get existing slot
            slot = self._db.query(TaskSlot).filter(
                TaskSlot.id == slot_id,
                TaskSlot.task_id == task_id
            ).first()

            if not slot:
                logger.warning(f"Slot {slot_id} not found for task {task_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Slot with id {slot_id} not found for task {task_id}"
                )
            
            # Validate updates
            if slot_data.hours is not None and slot_data.hours <= 0:
                raise ValueError("Slot hours must be positive")
            
            if slot_data.start_hour is not None:
                if slot_data.start_hour < 0 or slot_data.start_hour >= 24:
                    raise ValueError("Start hour must be between 0 and 24")
            
            # Check time range
            new_start_hour = slot_data.start_hour if slot_data.start_hour is not None else slot.start_hour
            new_hours = slot_data.hours if slot_data.hours is not None else slot.hours
            
            if new_start_hour and new_hours:
                if float(new_start_hour) + float(new_hours) > 24:
                    raise ValueError(
                        f"Slot time exceeds 24 hours: "
                        f"{new_start_hour} + {new_hours} = {float(new_start_hour) + float(new_hours)}"
                    )
            
            # Check if total slot hours would exceed estimated hours
            task = self._db.query(Task).filter(Task.id == task_id).first()
            if task and task.estimated_hours:
                existing_slots = self._db.query(TaskSlot).filter(
                    TaskSlot.task_id == task_id,
                    TaskSlot.id != slot_id  # Exclude current slot
                ).all()
                total_other_hours = sum(float(s.hours) for s in existing_slots if s.hours)
                new_total_hours = total_other_hours + float(new_hours)
                
                if new_total_hours > float(task.estimated_hours):
                    logger.warning(
                        f"Updated slot hours would exceed estimated hours for task {task_id}"
                    )
                    raise ValueError(
                        f"Total slot hours ({new_total_hours:.1f}) would exceed "
                        f"estimated hours ({float(task.estimated_hours):.1f})"
                    )
            
            # Update fields
            update_data = slot_data.model_dump(exclude_none=True)
            for field, value in update_data.items():
                setattr(slot, field, value)

            self._db.commit()
            self._db.refresh(slot)
            
            logger.info(f"Updated slot {slot_id} for task {task_id}")
            return slot
            
        except ValueError as e:
            self._db.rollback()
            logger.warning(f"Validation error updating slot {slot_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            # Re-raise HTTPExceptions
            raise
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Integrity error updating slot {slot_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Slot update failed due to data conflict"
            )
        except SQLAlchemyError as e:
            self._db.rollback()
            logger.error(f"Database error updating slot {slot_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update slot"
            )
        except Exception as e:
            self._db.rollback()
            logger.error(f"Unexpected error updating slot {slot_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    def delete_slot(self, task_id: int, slot_id: int) -> bool:
        """
        Delete a time slot
        
        Args:
            task_id: Task ID
            slot_id: Slot ID to delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            HTTPException: If deletion fails
        """
        try:
            # Validate IDs
            if task_id <= 0:
                raise ValueError("Task ID must be positive")
            
            if slot_id <= 0:
                raise ValueError("Slot ID must be positive")
            
            # Check if task exists
            task = self._db.query(Task).filter(Task.id == task_id).first()
            if not task:
                logger.warning(f"Task {task_id} not found for slot deletion")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task with id {task_id} not found"
                )

            # Get slot
            slot = self._db.query(TaskSlot).filter(
                TaskSlot.id == slot_id,
                TaskSlot.task_id == task_id
            ).first()

            if not slot:
                logger.warning(f"Slot {slot_id} not found for task {task_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Slot with id {slot_id} not found for task {task_id}"
                )

            # Check if this is the last slot
            total_slots = self._db.query(TaskSlot).filter(
                TaskSlot.task_id == task_id
            ).count()
            
            if total_slots <= 1:
                logger.warning(
                    f"Attempted to delete last slot {slot_id} for task {task_id}"
                )
                raise ValueError(
                    "Cannot delete the last slot. A task must have at least one slot."
                )

            # Delete slot
            slot_info = f"{slot.slot_date} {slot.start_hour}-{float(slot.start_hour) + float(slot.hours)}"
            self._db.delete(slot)
            self._db.commit()
            
            logger.info(f"Deleted slot {slot_id} for task {task_id}: {slot_info}")
            return True
            
        except ValueError as e:
            self._db.rollback()
            logger.warning(f"Validation error deleting slot {slot_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            # Re-raise HTTPExceptions
            raise
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Integrity error deleting slot {slot_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Slot deletion failed due to data conflict"
            )
        except SQLAlchemyError as e:
            self._db.rollback()
            logger.error(f"Database error deleting slot {slot_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete slot"
            )
        except Exception as e:
            self._db.rollback()
            logger.error(f"Unexpected error deleting slot {slot_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    def get_slots_by_task(self, task_id: int) -> List[TaskSlot]:
        """
        Get all time slots for a task
        
        Args:
            task_id: Task ID
            
        Returns:
            List of TaskSlot objects
            
        Raises:
            HTTPException: If query fails
        """
        try:
            # Validate task_id
            if task_id <= 0:
                raise ValueError("Task ID must be positive")
            
            slots = self._db.query(TaskSlot).filter(
                TaskSlot.task_id == task_id
            ).order_by(TaskSlot.slot_date, TaskSlot.start_hour).all()
            
            logger.info(f"Retrieved {len(slots)} slots for task {task_id}")
            return slots
            
        except ValueError as e:
            logger.warning(f"Validation error getting slots for task {task_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error getting slots for task {task_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve slots"
            )
        except Exception as e:
            logger.error(f"Unexpected error getting slots for task {task_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )
