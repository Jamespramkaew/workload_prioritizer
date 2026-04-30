from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from datetime import datetime
from typing import Optional, Any


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)
    display_name: str = Field(min_length=1, max_length=100)

    @field_validator("password")
    @classmethod
    def password_byte_limit(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("password must not exceed 72 bytes")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    display_name: str
    created_at: datetime
    google_connected: bool = False

    @model_validator(mode='before')
    @classmethod
    def compute_fields(cls, data: Any) -> Any:
        if hasattr(data, 'google_access_token'):
            return {
                'id': data.id,
                'email': data.email,
                'display_name': data.display_name,
                'created_at': data.created_at,
                'google_connected': bool(data.google_access_token),
            }
        return data

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
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
