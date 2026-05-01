from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from datetime import datetime
from typing import Optional, Any
import re


class UserRegister(BaseModel):
    """Schema for user registration with comprehensive validation"""
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=72,
        description="Password (8-72 characters, must include uppercase, lowercase, and number)"
    )
    display_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Display name (1-100 characters)"
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength and byte limit"""
        # Check byte limit (bcrypt limitation)
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 bytes")
        
        # Check minimum length
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        # Check for at least one digit
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one number")
        
        # Optional: Check for special character (uncomment if needed)
        # if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
        #     raise ValueError("Password must contain at least one special character")
        
        return v
    
    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v: str) -> str:
        """Validate and sanitize display name"""
        # Strip whitespace
        v = v.strip()
        if not v:
            raise ValueError("Display name cannot be empty or whitespace only")
        
        # Remove excessive whitespace
        v = ' '.join(v.split())
        
        # Check for invalid characters (allow letters, numbers, spaces, and common punctuation)
        if not re.match(r'^[a-zA-Z0-9\s\-_.]+$', v):
            raise ValueError(
                "Display name can only contain letters, numbers, spaces, hyphens, "
                "underscores, and periods"
            )
        
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")


class UserResponse(BaseModel):
    """Schema for user response"""
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
    """Schema for authentication token"""
    access_token: str
    token_type: str = "bearer"
    email: Optional[str]
    display_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserSettingsResponse(BaseModel):
    """Schema for user settings response"""
    chart_type: str
    capacity: int
    density: str

    model_config = {"from_attributes": True}


class UserSettingsUpdate(BaseModel):
    """Schema for updating user settings with validation"""
    chart_type: Optional[str] = Field(
        None,
        pattern="^(bar|line|pie)$",
        description="Chart type: bar, line, or pie"
    )
    capacity: Optional[int] = Field(
        None,
        ge=1,
        le=24,
        description="Daily work capacity in hours (1-24)"
    )
    density: Optional[str] = Field(
        None,
        pattern="^(low|medium|high)$",
        description="Display density: low, medium, or high"
    )
    
    @field_validator("chart_type")
    @classmethod
    def validate_chart_type(cls, v):
        """Validate chart type"""
        if v is not None:
            valid_types = ["bar", "line", "pie"]
            if v not in valid_types:
                raise ValueError(f"Chart type must be one of: {', '.join(valid_types)}")
        return v
    
    @field_validator("density")
    @classmethod
    def validate_density(cls, v):
        """Validate density"""
        if v is not None:
            valid_densities = ["low", "medium", "high"]
            if v not in valid_densities:
                raise ValueError(f"Density must be one of: {', '.join(valid_densities)}")
        return v
