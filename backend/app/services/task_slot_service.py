from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from typing import List

from app.models.task import Task, TaskSlot
from app.schemas.task_schema import TaskSlotCreate, TaskSlotUpdate


class TaskSlotService:
    """Service for TaskSlot operations"""
    
    def __init__(self, db: Session):
        """
        Initialize TaskSlotService with database session
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create_slot(self, task_id: int, slot_data: TaskSlotCreate) -> TaskSlot:
        """
        Create a new slot for a task
        
        Args:
            task_id: ID of the parent task
            slot_data: TaskSlotCreate schema with slot details
            
        Returns:
            TaskSlot: Created slot object
            
        Raises:
            HTTPException 404: If task not found
            HTTPException 500: If database operation fails
        """
        # Check if task exists
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found"
            )
        
        try:
            # Create new slot
            new_slot = TaskSlot(
                task_id=task_id,
                slot_date=slot_data.slot_date,
                start_hour=slot_data.start_hour,
                hours=slot_data.hours
            )
            
            # Save to database
            self.db.add(new_slot)
            self.db.commit()
            self.db.refresh(new_slot)
            
            return new_slot
            
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create slot: {str(e)}"
            )
    
    def update_slot(self, task_id: int, slot_id: int, slot_data: TaskSlotUpdate) -> TaskSlot:
        """
        Update an existing slot
        
        Args:
            task_id: ID of the parent task
            slot_id: ID of the slot to update
            slot_data: TaskSlotUpdate schema with fields to update
            
        Returns:
            TaskSlot: Updated slot object
            
        Raises:
            HTTPException 404: If slot not found
            HTTPException 500: If database operation fails
        """
        # Find slot by id and task_id
        slot = self.db.query(TaskSlot).filter(
            TaskSlot.id == slot_id,
            TaskSlot.task_id == task_id
        ).first()
        
        if not slot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Slot with id {slot_id} not found for task {task_id}"
            )
        
        try:
            # Update only fields that are provided (not None)
            update_data = slot_data.model_dump(exclude_none=True)
            for field, value in update_data.items():
                setattr(slot, field, value)
            
            # Save changes
            self.db.commit()
            self.db.refresh(slot)
            
            return slot
            
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update slot: {str(e)}"
            )
    
    def delete_slot(self, task_id: int, slot_id: int) -> dict:
        """
        Delete a slot (must have at least 1 slot remaining)
        
        Args:
            task_id: ID of the parent task
            slot_id: ID of the slot to delete
            
        Returns:
            dict: Success message
            
        Raises:
            HTTPException 404: If task or slot not found
            HTTPException 400: If trying to delete the last slot
            HTTPException 500: If database operation fails
        """
        # Check if task exists
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found"
            )
        
        # Find slot
        slot = self.db.query(TaskSlot).filter(
            TaskSlot.id == slot_id,
            TaskSlot.task_id == task_id
        ).first()
        
        if not slot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Slot with id {slot_id} not found for task {task_id}"
            )
        
        # Check if this is the last slot
        total_slots = self.db.query(TaskSlot).filter(TaskSlot.task_id == task_id).count()
        if total_slots <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last slot. A task must have at least one slot."
            )
        
        try:
            # Delete slot
            self.db.delete(slot)
            self.db.commit()
            
            return {"message": "Slot deleted successfully"}
            
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete slot: {str(e)}"
            )
    
    def get_slots_by_task(self, task_id: int) -> List[TaskSlot]:
        """
        Get all slots for a specific task
        
        Args:
            task_id: ID of the task
            
        Returns:
            List[TaskSlot]: List of slots belonging to the task
        """
        return self.db.query(TaskSlot).filter(TaskSlot.task_id == task_id).all()
