from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta

from app.core.database import get_db
from app.models.task import Task, TaskSlot
from app.schemas.task_schema import (
    TaskCreate, 
    TaskUpdate, 
    TaskResponse, 
    TaskSlotCreate
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=List[TaskResponse])
def list_tasks(
    week_offset: int = Query(0, description="Week offset from current week (0 = current week)"),
    status: str = Query("active", description="Filter by status: active, pending, completed, all"),
    db: Session = Depends(get_db)
):
    """
    List tasks filtered by week and status.
    - week_offset=0: current week
    - week_offset=1: next week
    - week_offset=-1: previous week
    - status="active": pending + in_progress tasks
    - status="all": all tasks
    """
    # Calculate week start and end dates
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday
    week_end = week_start + timedelta(days=6)  # Sunday
    
    # Apply week offset
    week_start = week_start + timedelta(weeks=week_offset)
    week_end = week_end + timedelta(weeks=week_offset)
    
    # Build query
    query = db.query(Task)
    
    # Filter by status
    if status == "active":
        query = query.filter(Task.status.in_(["pending", "in_progress"]))
    elif status != "all":
        query = query.filter(Task.status == status)
    
    # Filter by week (tasks that have deadline in the week OR have slots in the week)
    query = query.filter(
        (Task.deadline_date >= week_start) & (Task.deadline_date <= week_end)
    )
    
    tasks = query.order_by(Task.deadline_date, Task.importance.desc()).all()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a single task by ID"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    return task


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task_data: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task with optional slots"""
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
    db.add(task)
    db.flush()  # Get task ID
    
    # Create slots if provided
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


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_data: TaskUpdate, db: Session = Depends(get_db)):
    """Update a task (title, status)"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    
    # Update only provided fields
    if task_data.title is not None:
        task.title = task_data.title
    if task_data.status is not None:
        task.status = task_data.status
    
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    
    db.delete(task)
    db.commit()
    return None