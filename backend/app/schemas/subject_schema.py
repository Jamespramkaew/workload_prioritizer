from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SubjectBase(BaseModel):
    name: Optional[str] = None
    short_name: Optional[str] = None
    color: Optional[str] = None
    sort_order: int = 0


class SubjectCreate(SubjectBase):
    user_id: Optional[int] = None


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    short_name: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None


class SubjectResponse(SubjectBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True