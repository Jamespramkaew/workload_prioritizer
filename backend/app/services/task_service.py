from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta

from app.models.task import Task, TaskSlot
from app.schemas.task_schema import TaskCreate, TaskUpdate


class TaskService:
    
    @staticmethod
    def list_tasks(
        db: Session,
        week_offset: int = 0,
        status: str = "active"
    ) -> List[Task]:
        """List tasks filtered by week and status"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        week_start = week_start + timedelta(weeks=week_offset)
        week_end = week_end + timedelta(weeks=week_offset)
        
        query = db.query(Task)
        
        if status == "active":
            query = query.filter(Task.status.in_(["pending", "in_progress"]))
        elif status != "all":
            query = query.filter(Task.status == status)
        
        query = query.filter(
            (Task.deadline_date >= week_start) & (Task.deadline_date <= week_end)
        )
        
        return query.order_by(Task.deadline_date, Task.importance.desc()).all()
    
    @staticmethod
    def get_task(db: Session, task_id: int) -> Optional[Task]:
        """Get a single task by ID"""
        return db.query(Task).filter(Task.id == task_id).first()
    
    @staticmethod
    def create_task(db: Session, task_data: TaskCreate) -> Task:
        """Create a new task with optional slots"""
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
        db.add(task)
        db.flush()
        
        if task_data.slots:
            for slot_data in task_data.slots:
                slot = TaskSlot(
                    task_id=task.id,
                    slot_date=slot_data.slot_date,
                    start_hour=slot_data.start_hour,
                    hours=slot_data.hours
                )
                db.add(slot)
        
        db.commit()
        db.refresh(task)
        return task
    
    @staticmethod
    def update_task(db: Session, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
        """Update a task (title, status)"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None
        
        if task_data.title is not None:
            task.title = task_data.title
        if task_data.status is not None:
            task.status = task_data.status
        
        db.commit()
        db.refresh(task)
        return task
    
    @staticmethod
    def delete_task(db: Session, task_id: int) -> bool:
        """Delete a task"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return False
        
        db.delete(task)
        db.commit()
        return True