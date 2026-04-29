from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional

class UserResponse(BaseModel):
    id: int



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
