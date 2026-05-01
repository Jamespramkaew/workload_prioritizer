from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.task_schema import TaskCreate, TaskUpdate, TaskResponse
from app.services.task_service import TaskService


class TaskController:
    def __init__(self, db: Session):
        self._service = TaskService(db)

    def list_tasks(self, week_offset: Optional[int], status: str) -> List[TaskResponse]:
        return self._service.list_tasks(week_offset, status)

    def get_task(self, task_id: int) -> TaskResponse:
        task = self._service.get_task(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found"
            )
        return task

    def create_task(self, task_data: TaskCreate) -> TaskResponse:
        return self._service.create_task(task_data)

    def update_task(self, task_id: int, task_data: TaskUpdate) -> TaskResponse:
        task = self._service.update_task(task_id, task_data)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found"
            )
        return task

    def delete_task(self, task_id: int) -> None:
        success = self._service.delete_task(task_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found"
            )
