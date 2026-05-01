from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from datetime import date, datetime, timedelta


class TaskSlotBase(BaseModel):
    """Base schema for task time slots with validation"""
    slot_date: Optional[date] = Field(None, description="Date of the time slot")
    start_hour: Optional[float] = Field(
        None, 
        ge=0, 
        lt=24, 
        description="Start hour (0-23.99, e.g., 9.5 = 9:30 AM)"
    )
    hours: Optional[float] = Field(
        None, 
        gt=0, 
        le=24, 
        description="Duration in hours (must be positive, max 24)"
    )
    
    @field_validator('start_hour')
    @classmethod
    def validate_start_hour(cls, v):
        """Validate start hour is within valid range"""
        if v is not None:
            if v < 0 or v >= 24:
                raise ValueError('Start hour must be between 0 and 24')
            # Round to 2 decimal places (precision to minutes)
            v = round(v, 2)
        return v
    
    @field_validator('hours')
    @classmethod
    def validate_hours(cls, v):
        """Validate hours is positive and reasonable"""
        if v is not None:
            if v <= 0:
                raise ValueError('Hours must be positive')
            if v > 24:
                raise ValueError('Hours cannot exceed 24 hours per slot')
            # Round to 1 decimal place
            v = round(v, 1)
        return v
    
    @model_validator(mode='after')
    def validate_time_range(self):
        """Validate that start_hour + hours doesn't exceed 24"""
        if self.start_hour is not None and self.hours is not None:
            end_hour = self.start_hour + self.hours
            if end_hour > 24:
                raise ValueError(
                    f'Time slot exceeds 24 hours: {self.start_hour} + {self.hours} = {end_hour}'
                )
        return self


class TaskSlotCreate(TaskSlotBase):
    """Schema for creating a task slot - all fields required"""
    slot_date: date = Field(..., description="Date of the time slot (required)")
    start_hour: float = Field(..., ge=0, lt=24, description="Start hour (required)")
    hours: float = Field(..., gt=0, le=24, description="Duration in hours (required)")


class TaskSlotUpdate(BaseModel):
    """Schema for updating a task slot - all fields optional"""
    slot_date: Optional[date] = Field(None, description="Date of the time slot")
    start_hour: Optional[float] = Field(None, ge=0, lt=24, description="Start hour")
    hours: Optional[float] = Field(None, gt=0, le=24, description="Duration in hours")


class TaskSlotResponse(TaskSlotBase):
    """Schema for task slot response"""
    id: int
    task_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    """Base schema for tasks with comprehensive validation"""
    title: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=500,
        description="Task title (1-500 characters)"
    )
    deadline_date: Optional[date] = Field(
        None, 
        description="Task deadline date"
    )
    difficulty: Optional[int] = Field(
        None, 
        ge=1, 
        le=5, 
        description="Difficulty level (1=easiest, 5=hardest)"
    )
    importance: Optional[int] = Field(
        None, 
        ge=1, 
        le=5, 
        description="Importance level (1=lowest, 5=highest)"
    )
    comfortable: Optional[bool] = Field(
        None, 
        description="Whether user is comfortable with this task"
    )
    estimated_hours: Optional[float] = Field(
        None, 
        gt=0, 
        le=1000,
        description="Estimated hours to complete (must be positive, max 1000)"
    )
    status: str = Field(
        "pending",
        pattern="^(pending|in_progress|completed|cancelled)$",
        description="Task status: pending, in_progress, completed, or cancelled"
    )
    subject_id: Optional[int] = Field(
        None, 
        gt=0, 
        description="Subject/Course ID (must be positive)"
    )
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Validate and sanitize title"""
        if v is not None:
            # Strip whitespace
            v = v.strip()
            if not v:
                raise ValueError('Title cannot be empty or whitespace only')
            # Remove excessive whitespace
            v = ' '.join(v.split())
            # Check length after cleaning
            if len(v) > 500:
                raise ValueError('Title cannot exceed 500 characters')
        return v
    
    @field_validator('deadline_date')
    @classmethod
    def validate_deadline(cls, v):
        """Validate deadline date is reasonable"""
        if v is not None:
            # Allow past dates for historical tasks, but not too far
            if v < date.today() - timedelta(days=365):
                raise ValueError('Deadline cannot be more than 1 year in the past')
            # Warn if deadline is too far in future (10 years)
            if v > date.today() + timedelta(days=3650):
                raise ValueError('Deadline cannot be more than 10 years in the future')
        return v
    
    @field_validator('estimated_hours')
    @classmethod
    def validate_estimated_hours(cls, v):
        """Validate estimated hours"""
        if v is not None:
            if v <= 0:
                raise ValueError('Estimated hours must be positive')
            if v > 1000:
                raise ValueError('Estimated hours cannot exceed 1000')
            # Round to 1 decimal place
            v = round(v, 1)
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate status is one of allowed values"""
        valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v


class TaskCreate(TaskBase):
    """Schema for creating a task - required fields are non-optional"""
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=500,
        description="Task title (required)"
    )
    deadline_date: date = Field(..., description="Task deadline (required)")
    difficulty: int = Field(..., ge=1, le=5, description="Difficulty level 1-5 (required)")
    importance: int = Field(..., ge=1, le=5, description="Importance level 1-5 (required)")
    estimated_hours: float = Field(
        ..., 
        gt=0, 
        le=1000,
        description="Estimated hours (required)"
    )
    
    user_id: Optional[int] = Field(None, gt=0, description="User ID")
    slots: Optional[List[TaskSlotCreate]] = Field(
        default_factory=list,
        description="Time slots for this task"
    )
    
    @model_validator(mode='after')
    def validate_slots_total(self):
        """Validate that total slot hours don't exceed estimated hours"""
        if self.slots:
            total_slot_hours = sum(slot.hours for slot in self.slots)
            if total_slot_hours > self.estimated_hours:
                raise ValueError(
                    f'Total slot hours ({total_slot_hours}) cannot exceed '
                    f'estimated hours ({self.estimated_hours})'
                )
        return self


class TaskUpdate(BaseModel):
    """Schema for updating a task - all fields optional"""
    title: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=500,
        description="Task title"
    )
    status: Optional[str] = Field(
        None,
        pattern="^(pending|in_progress|completed|cancelled)$",
        description="Task status"
    )
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Validate and sanitize title"""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('Title cannot be empty or whitespace only')
            v = ' '.join(v.split())
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate status"""
        if v is not None:
            valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
            if v not in valid_statuses:
                raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v


class TaskResponse(TaskBase):
    """Schema for task response"""
    id: int
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    task_slots: List[TaskSlotResponse] = []

    class Config:
        from_attributes = True
