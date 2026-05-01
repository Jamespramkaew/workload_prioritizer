from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.subject_schema import SubjectCreate, SubjectUpdate, SubjectResponse
from app.services.subject_service import SubjectService
from app.middleware.rate_limit import limiter, RateLimits

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("", response_model=List[SubjectResponse])
@limiter.limit(RateLimits.LIST)
def list_subjects(
    request: Request,
    user_id: int = Query(..., description="User ID to filter subjects"),
    db: Session = Depends(get_db)
):
    return SubjectService(db).list_subjects(user_id)


@router.get("/{subject_id}", response_model=SubjectResponse)
@limiter.limit(RateLimits.READ)
def get_subject(request: Request, subject_id: int, db: Session = Depends(get_db)):
    subject = SubjectService(db).get_subject(subject_id)
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with id {subject_id} not found"
        )
    return subject


@router.post("", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RateLimits.CREATE)
def create_subject(request: Request, subject_data: SubjectCreate, db: Session = Depends(get_db)):
    return SubjectService(db).create_subject(subject_data)


@router.patch("/{subject_id}", response_model=SubjectResponse)
@limiter.limit(RateLimits.UPDATE)
def update_subject(request: Request, subject_id: int, subject_data: SubjectUpdate, db: Session = Depends(get_db)):
    subject = SubjectService(db).update_subject(subject_id, subject_data)
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with id {subject_id} not found"
        )
    return subject


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(RateLimits.DELETE)
def delete_subject(request: Request, subject_id: int, db: Session = Depends(get_db)):
    success = SubjectService(db).delete_subject(subject_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with id {subject_id} not found"
        )
    return None
