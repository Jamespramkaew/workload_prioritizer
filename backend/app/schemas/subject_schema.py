from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re


class SubjectBase(BaseModel):
    """Base schema for subjects with validation"""
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Subject name (1-200 characters)"
    )
    short_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=20,
        description="Short name/abbreviation (1-20 characters)"
    )
    color: Optional[str] = Field(
        None,
        pattern="^#[0-9A-Fa-f]{6}$",
        description="Hex color code (e.g., #FF6B6B)"
    )
    sort_order: int = Field(
        0,
        ge=0,
        description="Display order (0 or positive)"
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate and sanitize subject name"""
        if v is not None:
            # Strip whitespace
            v = v.strip()
            if not v:
                raise ValueError('Subject name cannot be empty or whitespace only')
            # Remove excessive whitespace
            v = ' '.join(v.split())
            # Check length
            if len(v) > 200:
                raise ValueError('Subject name cannot exceed 200 characters')
        return v
    
    @field_validator('short_name')
    @classmethod
    def validate_short_name(cls, v):
        """Validate and sanitize short name"""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('Short name cannot be empty or whitespace only')
            # Remove whitespace from short name
            v = ''.join(v.split())
            if len(v) > 20:
                raise ValueError('Short name cannot exceed 20 characters')
        return v
    
    @field_validator('color')
    @classmethod
    def validate_color(cls, v):
        """Validate color is a valid hex code"""
        if v is not None:
            # Convert to uppercase
            v = v.upper()
            # Check format
            if not re.match(r'^#[0-9A-F]{6}$', v):
                raise ValueError(
                    'Color must be a valid hex color code (e.g., #FF6B6B, #123ABC)'
                )
        return v
    
    @field_validator('sort_order')
    @classmethod
    def validate_sort_order(cls, v):
        """Validate sort order is non-negative"""
        if v < 0:
            raise ValueError('Sort order cannot be negative')
        return v


class SubjectCreate(SubjectBase):
    """Schema for creating a subject - required fields are non-optional"""
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Subject name (required)"
    )
    short_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=20,
        description="Short name (optional, will be auto-generated if not provided)"
    )
    color: Optional[str] = Field(
        None,
        pattern="^#[0-9A-Fa-f]{6}$",
        description="Hex color code (optional, will be auto-assigned if not provided)"
    )
    
    user_id: Optional[int] = Field(None, gt=0, description="User ID")


class SubjectUpdate(BaseModel):
    """Schema for updating a subject - all fields optional"""
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Subject name"
    )
    short_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=20,
        description="Short name"
    )
    color: Optional[str] = Field(
        None,
        pattern="^#[0-9A-Fa-f]{6}$",
        description="Hex color code"
    )
    sort_order: Optional[int] = Field(
        None,
        ge=0,
        description="Display order"
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate name"""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('Subject name cannot be empty')
            v = ' '.join(v.split())
        return v
    
    @field_validator('short_name')
    @classmethod
    def validate_short_name(cls, v):
        """Validate short name"""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('Short name cannot be empty')
            v = ''.join(v.split())
        return v
    
    @field_validator('color')
    @classmethod
    def validate_color(cls, v):
        """Validate color"""
        if v is not None:
            v = v.upper()
            if not re.match(r'^#[0-9A-F]{6}$', v):
                raise ValueError('Color must be a valid hex color code')
        return v


class SubjectResponse(SubjectBase):
    """Schema for subject response"""
    id: int
    user_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True