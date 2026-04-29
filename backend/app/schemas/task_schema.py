from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date
from decimal import Decimal


# ==================== TaskSlot Schemas ====================

class TaskSlotBase(BaseModel):
    """Base schema for TaskSlot with common fields"""
    slot_date: date = Field(..., description="Date of the slot (YYYY-MM-DD)")
    start_hour: Decimal = Field(..., ge=0, lt=24, description="Start hour (0-23.99)")
    hours: Decimal = Field(..., gt=0, le=12, description="Duration in hours (0.5-12)")
    
    @field_validator('start_hour')
    @classmethod
    def validate_start_hour(cls, v):
        """Validate start_hour is between 0 and 23.99"""
        if v < 0 or v >= 24:
            raise ValueError('start_hour must be between 0 and 23.99')
        return v
    
    @field_validator('hours')
    @classmethod
    def validate_hours(cls, v):
        """Validate hours is positive and reasonable"""
        if v <= 0:
            raise ValueError('hours must be greater than 0')
        if v > 12:
            raise ValueError('hours cannot exceed 12 per slot')
        return v


class TaskSlotCreate(TaskSlotBase):
    """Schema for creating a new TaskSlot"""
    pass


class TaskSlotUpdate(BaseModel):
    """Schema for updating a TaskSlot (all fields optional)"""
    slot_date: Optional[date] = Field(None, description="Date of the slot")
    start_hour: Optional[Decimal] = Field(None, ge=0, lt=24, description="Start hour")
    hours: Optional[Decimal] = Field(None, gt=0, le=12, description="Duration in hours")
    
    @field_validator('start_hour')
    @classmethod
    def validate_start_hour(cls, v):
        if v is not None and (v < 0 or v >= 24):
            raise ValueError('start_hour must be between 0 and 23.99')
        return v
    
    @field_validator('hours')
    @classmethod
    def validate_hours(cls, v):
        if v is not None:
            if v <= 0:
                raise ValueError('hours must be greater than 0')
            if v > 12:
                raise ValueError('hours cannot exceed 12 per slot')
        return v


class TaskSlotResponse(TaskSlotBase):
    """Schema for TaskSlot response"""
    id: int = Field(..., description="Slot ID")
    task_id: int = Field(..., description="Parent task ID")
    
    class Config:
        from_attributes = True  # Pydantic v2 (แทน orm_mode = True)


# ==================== Task Schemas ====================

class TaskBase(BaseModel):
    """Base schema for Task with common fields"""
    title: str = Field(..., min_length=1, max_length=500, description="Task title")
    subject_id: int = Field(..., description="Subject ID")
    deadline_date: date = Field(..., description="Deadline date")
    difficulty: int = Field(..., ge=1, le=5, description="Difficulty level (1-5)")
    importance: int = Field(..., ge=1, le=5, description="Importance level (1-5)")
    comfortable: bool = Field(..., description="Is user comfortable with this task?")
    estimated_hours: Decimal = Field(..., gt=0, description="Estimated hours to complete")
    
    @field_validator('difficulty', 'importance')
    @classmethod
    def validate_rating(cls, v):
        """Validate difficulty and importance are between 1-5"""
        if v < 1 or v > 5:
            raise ValueError('Rating must be between 1 and 5')
        return v


class TaskCreate(TaskBase):
    """Schema for creating a new Task with slots"""
    slots: List[TaskSlotCreate] = Field(
        ..., 
        min_length=1, 
        description="At least one slot is required"
    )
    
    @field_validator('slots')
    @classmethod
    def validate_slots(cls, v):
        """Validate at least one slot exists"""
        if not v or len(v) == 0:
            raise ValueError('At least one slot is required')
        return v


class TaskUpdate(BaseModel):
    """Schema for updating a Task (all fields optional except slots)"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    subject_id: Optional[int] = None
    deadline_date: Optional[date] = None
    difficulty: Optional[int] = Field(None, ge=1, le=5)
    importance: Optional[int] = Field(None, ge=1, le=5)
    comfortable: Optional[bool] = None
    estimated_hours: Optional[Decimal] = Field(None, gt=0)
    status: Optional[str] = Field(None, pattern="^(active|done|archived)$")
    
    @field_validator('difficulty', 'importance')
    @classmethod
    def validate_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Rating must be between 1 and 5')
        return v


class TaskResponse(TaskBase):
    """Schema for Task response with slots"""
    id: int = Field(..., description="Task ID")
    user_id: int = Field(..., description="Owner user ID")
    status: str = Field(..., description="Task status (active/done/archived)")
    slots: List[TaskSlotResponse] = Field(default_factory=list, description="Task slots")
    
    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Schema for listing multiple tasks"""
    tasks: List[TaskResponse]
    total: int = Field(..., description="Total number of tasks")
    week_start: Optional[date] = Field(None, description="Week start date")
    week_end: Optional[date] = Field(None, description="Week end date")
