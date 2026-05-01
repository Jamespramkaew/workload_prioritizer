from sqlalchemy.orm import Session

from app.schemas.task_schema import TaskSlotCreate, TaskSlotUpdate, TaskSlotResponse
from app.services.task_slot_service import TaskSlotService


class TaskSlotController:
    def __init__(self, db: Session):
        self._service = TaskSlotService(db)

    def create_slot(self, task_id: int, slot_data: TaskSlotCreate) -> TaskSlotResponse:
        return self._service.create_slot(task_id, slot_data)

    def update_slot(self, task_id: int, slot_id: int, slot_data: TaskSlotUpdate) -> TaskSlotResponse:
        return self._service.update_slot(task_id, slot_id, slot_data)

    def delete_slot(self, task_id: int, slot_id: int) -> None:
        self._service.delete_slot(task_id, slot_id)
