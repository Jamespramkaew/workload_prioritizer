from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserResponse(BaseModel):
    id: int
    email: Optional[str]
    display_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserSettingsResponse(BaseModel):
    chart_type: str
    capacity: int
    density: str

    model_config = {"from_attributes": True}


class UserSettingsUpdate(BaseModel):
    chart_type: Optional[str] = None
    capacity: Optional[int] = None
    density: Optional[str] = None
