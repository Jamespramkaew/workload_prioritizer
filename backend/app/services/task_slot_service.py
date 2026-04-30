from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from typing import List

from app.models.task import Task, TaskSlot
from app.schemas.task_schema import TaskSlotCreate, TaskSlotUpdate


class TaskSlotService:
    def __init__(self, db: Session):
        self._db = db

    @property
    def db(self) -> Session:
        return self._db

    def create_slot(self, task_id: int, slot_data: TaskSlotCreate) -> TaskSlot:
        task = self._db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found"
            )

        try:
            new_slot = TaskSlot(
                task_id=task_id,
                slot_date=slot_data.slot_date,
                start_hour=slot_data.start_hour,
                hours=slot_data.hours
            )
            self._db.add(new_slot)
            self._db.commit()
            self._db.refresh(new_slot)
            return new_slot

        except SQLAlchemyError as e:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create slot: {str(e)}"
            )

    def update_slot(self, task_id: int, slot_id: int, slot_data: TaskSlotUpdate) -> TaskSlot:
        slot = self._db.query(TaskSlot).filter(
            TaskSlot.id == slot_id,
            TaskSlot.task_id == task_id
        ).first()

        if not slot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Slot with id {slot_id} not found for task {task_id}"
            )

        try:
            update_data = slot_data.model_dump(exclude_none=True)
            for field, value in update_data.items():
                setattr(slot, field, value)

            self._db.commit()
            self._db.refresh(slot)
            return slot

        except SQLAlchemyError as e:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update slot: {str(e)}"
            )

    def delete_slot(self, task_id: int, slot_id: int) -> dict:
        task = self._db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found"
            )

        slot = self._db.query(TaskSlot).filter(
            TaskSlot.id == slot_id,
            TaskSlot.task_id == task_id
        ).first()

        if not slot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Slot with id {slot_id} not found for task {task_id}"
            )

        total_slots = self._db.query(TaskSlot).filter(TaskSlot.task_id == task_id).count()
        if total_slots <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last slot. A task must have at least one slot."
            )

        try:
            self._db.delete(slot)
            self._db.commit()
            return {"message": "Slot deleted successfully"}

        except SQLAlchemyError as e:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete slot: {str(e)}"
            )

    def get_slots_by_task(self, task_id: int) -> List[TaskSlot]:
        return self._db.query(TaskSlot).filter(TaskSlot.task_id == task_id).all()
