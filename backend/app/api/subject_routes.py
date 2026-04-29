from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.subject import Subject
from app.schemas.subject_schema import (
    SubjectCreate,
    SubjectUpdate,
    SubjectResponse
)

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("", response_model=List[SubjectResponse])
def list_subjects(
    user_id: int = Query(..., description="User ID to filter subjects"),
    db: Session = Depends(get_db)
):
    """
    List all subjects for a specific user.
    """
    subjects = db.query(Subject).filter(
        Subject.user_id == user_id
    ).order_by(Subject.sort_order, Subject.name).all()
    return subjects


@router.get("/{subject_id}", response_model=SubjectResponse)
def get_subject(subject_id: int, db: Session = Depends(get_db)):
    """Get a single subject by ID"""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with id {subject_id} not found"
        )
    return subject


@router.post("", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
def create_subject(subject_data: SubjectCreate, db: Session = Depends(get_db)):
    """Create a new subject"""
    subject = Subject(
        user_id=subject_data.user_id,
        name=subject_data.name,
        short_name=subject_data.short_name,
        color=subject_data.color,
        sort_order=subject_data.sort_order
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


@router.patch("/{subject_id}", response_model=SubjectResponse)
def update_subject(subject_id: int, subject_data: SubjectUpdate, db: Session = Depends(get_db)):
    """Update a subject (name, short_name, color, sort_order)"""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with id {subject_id} not found"
        )
    
    # Update only provided fields
    if subject_data.name is not None:
        subject.name = subject_data.name
    if subject_data.short_name is not None:
        subject.short_name = subject_data.short_name
    if subject_data.color is not None:
        subject.color = subject_data.color
    if subject_data.sort_order is not None:
        subject.sort_order = subject_data.sort_order
    
    db.commit()
    db.refresh(subject)
    return subject


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(subject_id: int, db: Session = Depends(get_db)):
    """Delete a subject"""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with id {subject_id} not found"
        )
    
    db.delete(subject)
    db.commit()
    return None