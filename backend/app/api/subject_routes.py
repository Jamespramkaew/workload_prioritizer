from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List
import logging

from app.core.database import get_db
from app.schemas.subject_schema import SubjectCreate, SubjectUpdate, SubjectResponse
from app.services.subject_service import SubjectService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("", response_model=List[SubjectResponse])
def list_subjects(
    request: Request,
    user_id: int = Query(..., gt=0, description="User ID to filter subjects (must be positive)"),
    db: Session = Depends(get_db)
):
    """
    List all subjects for a specific user
    
    Args:
        user_id: User ID (must be positive)
        db: Database session
        
    Returns:
        List of subjects
        
    Raises:
        HTTPException 400: Invalid user ID
        HTTPException 500: Database error
    """
    try:
        logger.info(f"Listing subjects for user {user_id}")
        service = SubjectService(db)
        subjects = service.list_subjects(user_id)
        logger.info(f"Successfully listed {len(subjects)} subjects for user {user_id}")
        return subjects
        
    except HTTPException:
        # Re-raise HTTPExceptions from service layer
        raise
    except Exception as e:
        logger.error(f"Unexpected error in list_subjects endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subjects"
        )


@router.get("/{subject_id}", response_model=SubjectResponse)
def get_subject(
    request: Request,
    subject_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single subject by ID
    
    Args:
        subject_id: Subject ID
        db: Database session
        
    Returns:
        Subject object
        
    Raises:
        HTTPException 400: Invalid subject ID
        HTTPException 404: Subject not found
        HTTPException 500: Database error
    """
    try:
        logger.info(f"Getting subject {subject_id}")
        service = SubjectService(db)
        subject = service.get_subject(subject_id)
        
        if not subject:
            logger.warning(f"Subject {subject_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subject with id {subject_id} not found"
            )
        
        logger.info(f"Successfully retrieved subject {subject_id}")
        return subject
        
    except HTTPException:
        # Re-raise HTTPExceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_subject endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subject"
        )


@router.post("", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
def create_subject(
    request: Request,
    subject_data: SubjectCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new subject
    
    Args:
        subject_data: Subject creation data
        db: Database session
        
    Returns:
        Created subject
        
    Raises:
        HTTPException 400: Invalid data
        HTTPException 409: Duplicate subject name
        HTTPException 422: Validation error
        HTTPException 500: Database error
    """
    try:
        logger.info(f"Creating subject: {subject_data.name}")
        service = SubjectService(db)
        subject = service.create_subject(subject_data)
        logger.info(f"Successfully created subject {subject.id}: {subject.name}")
        return subject
        
    except HTTPException:
        # Re-raise HTTPExceptions from service layer
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_subject endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subject"
        )


@router.patch("/{subject_id}", response_model=SubjectResponse)
def update_subject(
    request: Request,
    subject_id: int,
    subject_data: SubjectUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a subject
    
    Args:
        subject_id: Subject ID to update
        subject_data: Update data
        db: Database session
        
    Returns:
        Updated subject
        
    Raises:
        HTTPException 400: Invalid data
        HTTPException 404: Subject not found
        HTTPException 409: Duplicate subject name
        HTTPException 422: Validation error
        HTTPException 500: Database error
    """
    try:
        logger.info(f"Updating subject {subject_id}")
        service = SubjectService(db)
        subject = service.update_subject(subject_id, subject_data)
        
        if not subject:
            logger.warning(f"Subject {subject_id} not found for update")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subject with id {subject_id} not found"
            )
        
        logger.info(f"Successfully updated subject {subject_id}")
        return subject
        
    except HTTPException:
        # Re-raise HTTPExceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in update_subject endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update subject"
        )


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(
    request: Request,
    subject_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a subject
    
    Args:
        subject_id: Subject ID to delete
        db: Database session
        
    Returns:
        None (204 No Content)
        
    Raises:
        HTTPException 400: Invalid subject ID or has associated tasks
        HTTPException 404: Subject not found
        HTTPException 409: Cannot delete due to foreign key constraint
        HTTPException 500: Database error
    """
    try:
        logger.info(f"Deleting subject {subject_id}")
        service = SubjectService(db)
        success = service.delete_subject(subject_id)
        
        if not success:
            logger.warning(f"Subject {subject_id} not found for deletion")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subject with id {subject_id} not found"
            )
        
        logger.info(f"Successfully deleted subject {subject_id}")
        return None
        
    except HTTPException:
        # Re-raise HTTPExceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in delete_subject endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete subject"
        )
