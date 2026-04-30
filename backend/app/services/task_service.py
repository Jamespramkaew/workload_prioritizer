from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta

from app.models.task import Task, TaskSlot
from app.schemas.task_schema import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, db: Session):
        self._db = db

    @property
    def db(self) -> Session:
        return self._db

    def list_tasks(
        self,
        week_offset: Optional[int] = None,
        status: str = "active"
    ) -> List[Task]:
        query = self._db.query(Task)

        if status == "active":
            query = query.filter(Task.status.in_(["pending", "in_progress"]))
        elif status != "all":
            query = query.filter(Task.status == status)

        if week_offset is not None:
            today = date.today()
            week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
            week_end = week_start + timedelta(days=6)
            query = query.filter(Task.deadline_date >= week_start, Task.deadline_date <= week_end)

        return query.order_by(Task.deadline_date, Task.importance.desc()).all()

    def get_task(self, task_id: int) -> Optional[Task]:
        return self._db.query(Task).filter(Task.id == task_id).first()

    def create_task(self, task_data: TaskCreate) -> Task:
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

        if task_data.slots:
            for slot_data in task_data.slots:
                slot = TaskSlot(
                    task_id=task.id,
                    slot_date=slot_data.slot_date,
                    start_hour=slot_data.start_hour,
                    hours=slot_data.hours
                )
                self._db.add(slot)

        self._db.commit()
        self._db.refresh(task)
        return task

    def update_task(self, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
        task = self._db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None

        if task_data.title is not None:
            task.title = task_data.title
        if task_data.status is not None:
            task.status = task_data.status

        self._db.commit()
        self._db.refresh(task)
        return task

    def delete_task(self, task_id: int) -> bool:
        task = self._db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return False

        self._db.delete(task)
        self._db.commit()
        return True
