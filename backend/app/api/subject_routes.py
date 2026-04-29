from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.subject_schema import SubjectCreate, SubjectUpdate, SubjectResponse
from app.services.subject_service import SubjectService

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("", response_model=List[SubjectResponse])
def list_subjects(
    user_id: int = Query(..., description="User ID to filter subjects"),
    db: Session = Depends(get_db)
):
    """
    List all subjects for a specific user.
    """
    return SubjectService.list_subjects(db, user_id)


@router.get("/{subject_id}", response_model=SubjectResponse)
def get_subject(subject_id: int, db: Session = Depends(get_db)):
    """Get a single subject by ID"""
    subject = SubjectService.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with id {subject_id} not found"
        )
    return subject


@router.post("", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
def create_subject(subject_data: SubjectCreate, db: Session = Depends(get_db)):
    """Create a new subject"""
    return SubjectService.create_subject(db, subject_data)


@router.patch("/{subject_id}", response_model=SubjectResponse)
def update_subject(subject_id: int, subject_data: SubjectUpdate, db: Session = Depends(get_db)):
    """Update a subject (name, short_name, color, sort_order)"""
    subject = SubjectService.update_subject(db, subject_id, subject_data)
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with id {subject_id} not found"
        )
    return subject


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(subject_id: int, db: Session = Depends(get_db)):
    """Delete a subject"""
    success = SubjectService.delete_subject(db, subject_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with id {subject_id} not found"
        )
    return None