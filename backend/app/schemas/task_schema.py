from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


# TaskSlot Schema
class TaskSlotBase(BaseModel):
    slot_date: Optional[date] = None
    start_hour: Optional[float] = None
    hours: Optional[float] = None


class TaskSlotCreate(TaskSlotBase):
    pass


class TaskSlotResponse(TaskSlotBase):
    id: int
    task_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Task Schema
class TaskBase(BaseModel):
    title: Optional[str] = None
    deadline_date: Optional[date] = None
    difficulty: Optional[int] = None
    importance: Optional[int] = None
    comfortable: Optional[bool] = None
    estimated_hours: Optional[float] = None
    status: str = "pending"
    subject_id: Optional[int] = None


class TaskCreate(TaskBase):
    user_id: Optional[int] = None
    slots: Optional[List[TaskSlotCreate]] = []


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None


class TaskResponse(TaskBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    task_slots: List[TaskSlotResponse] = []

    class Config:
        from_attributes = True