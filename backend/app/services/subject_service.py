from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from fastapi import HTTPException, status
from typing import List, Optional
import logging

from app.models.subject import Subject
from app.schemas.subject_schema import SubjectCreate, SubjectUpdate

logger = logging.getLogger(__name__)


class SubjectService:
    """
    Subject Service with comprehensive error handling
    Manages subject operations with transaction management and validation
    """
    
    def __init__(self, db: Session):
        """
        Initialize service with database session
        
        Args:
            db: SQLAlchemy database session
        """
        self._db = db

    @property
    def db(self) -> Session:
        """Get database session"""
        return self._db

    def list_subjects(self, user_id: int) -> List[Subject]:
        """
        List all subjects for a specific user
        
        Args:
            user_id: User ID to filter subjects
            
        Returns:
            List of Subject objects
            
        Raises:
            HTTPException: If database query fails
        """
        try:
            # Validate user_id
            if user_id <= 0:
                raise ValueError("User ID must be positive")
            
            subjects = self._db.query(Subject).filter(
                Subject.user_id == user_id
            ).order_by(Subject.sort_order, Subject.name).all()
            
            logger.info(f"Listed {len(subjects)} subjects for user {user_id}")
            return subjects
            
        except ValueError as e:
            logger.warning(f"Validation error listing subjects: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error listing subjects for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve subjects"
            )
        except Exception as e:
            logger.error(f"Unexpected error listing subjects: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    def get_subject(self, subject_id: int) -> Optional[Subject]:
        """
        Get a single subject by ID
        
        Args:
            subject_id: Subject ID
            
        Returns:
            Subject object or None if not found
            
        Raises:
            HTTPException: If database query fails
        """
        try:
            # Validate subject_id
            if subject_id <= 0:
                raise ValueError("Subject ID must be positive")
            
            subject = self._db.query(Subject).filter(Subject.id == subject_id).first()
            
            if subject:
                logger.info(f"Retrieved subject {subject_id}: {subject.name}")
            else:
                logger.info(f"Subject {subject_id} not found")
            
            return subject
            
        except ValueError as e:
            logger.warning(f"Validation error getting subject: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error getting subject {subject_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve subject"
            )
        except Exception as e:
            logger.error(f"Unexpected error getting subject {subject_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    def create_subject(self, subject_data: SubjectCreate) -> Subject:
        """
        Create a new subject with transaction management
        
        Args:
            subject_data: Subject creation data
            
        Returns:
            Created Subject object
            
        Raises:
            HTTPException: If creation fails
        """
        try:
            # Additional validation
            if subject_data.user_id and subject_data.user_id <= 0:
                raise ValueError("User ID must be positive")
            
            if not subject_data.name or not subject_data.name.strip():
                raise ValueError("Subject name is required")
            
            # Check for duplicate subject name for the same user
            if subject_data.user_id:
                existing = self._db.query(Subject).filter(
                    Subject.user_id == subject_data.user_id,
                    Subject.name == subject_data.name
                ).first()
                
                if existing:
                    raise ValueError(f"Subject '{subject_data.name}' already exists for this user")
            
            # Create subject
            subject = Subject(
                user_id=subject_data.user_id,
                name=subject_data.name,
                short_name=subject_data.short_name,
                color=subject_data.color,
                sort_order=subject_data.sort_order
            )
            
            self._db.add(subject)
            self._db.commit()
            self._db.refresh(subject)
            
            logger.info(f"Created subject {subject.id}: {subject.name}")
            return subject
            
        except ValueError as e:
            self._db.rollback()
            logger.warning(f"Validation error creating subject: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Integrity error creating subject: {str(e)}")
            
            # Check for specific constraint violations
            error_msg = str(e.orig).lower()
            if 'unique' in error_msg or 'duplicate' in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A subject with this name already exists"
                )
            elif 'foreign key' in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid user ID"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Subject creation failed due to data conflict"
                )
        except SQLAlchemyError as e:
            self._db.rollback()
            logger.error(f"Database error creating subject: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create subject"
            )
        except Exception as e:
            self._db.rollback()
            logger.error(f"Unexpected error creating subject: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    def update_subject(self, subject_id: int, subject_data: SubjectUpdate) -> Optional[Subject]:
        """
        Update a subject with transaction management
        
        Args:
            subject_id: Subject ID to update
            subject_data: Update data
            
        Returns:
            Updated Subject object or None if not found
            
        Raises:
            HTTPException: If update fails
        """
        try:
            # Validate subject_id
            if subject_id <= 0:
                raise ValueError("Subject ID must be positive")
            
            # Get existing subject
            subject = self._db.query(Subject).filter(Subject.id == subject_id).first()
            if not subject:
                logger.info(f"Subject {subject_id} not found for update")
                return None
            
            # Validate updates
            if subject_data.name is not None:
                if not subject_data.name.strip():
                    raise ValueError("Subject name cannot be empty")
                
                # Check for duplicate name (excluding current subject)
                existing = self._db.query(Subject).filter(
                    Subject.user_id == subject.user_id,
                    Subject.name == subject_data.name,
                    Subject.id != subject_id
                ).first()
                
                if existing:
                    raise ValueError(f"Subject '{subject_data.name}' already exists for this user")
            
            # Update fields
            if subject_data.name is not None:
                subject.name = subject_data.name
            if subject_data.short_name is not None:
                subject.short_name = subject_data.short_name
            if subject_data.color is not None:
                subject.color = subject_data.color
            if subject_data.sort_order is not None:
                subject.sort_order = subject_data.sort_order

            self._db.commit()
            self._db.refresh(subject)
            
            logger.info(f"Updated subject {subject_id}: {subject.name}")
            return subject
            
        except ValueError as e:
            self._db.rollback()
            logger.warning(f"Validation error updating subject {subject_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Integrity error updating subject {subject_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Subject update failed due to data conflict"
            )
        except SQLAlchemyError as e:
            self._db.rollback()
            logger.error(f"Database error updating subject {subject_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update subject"
            )
        except Exception as e:
            self._db.rollback()
            logger.error(f"Unexpected error updating subject {subject_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    def delete_subject(self, subject_id: int) -> bool:
        """
        Delete a subject with transaction management
        
        Args:
            subject_id: Subject ID to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            HTTPException: If deletion fails
        """
        try:
            # Validate subject_id
            if subject_id <= 0:
                raise ValueError("Subject ID must be positive")
            
            subject = self._db.query(Subject).filter(Subject.id == subject_id).first()
            if not subject:
                logger.info(f"Subject {subject_id} not found for deletion")
                return False
            
            # Check if subject has associated tasks
            if hasattr(subject, 'tasks') and subject.tasks:
                logger.warning(f"Attempted to delete subject {subject_id} with {len(subject.tasks)} tasks")
                raise ValueError(
                    f"Cannot delete subject '{subject.name}' because it has {len(subject.tasks)} associated tasks. "
                    "Please delete or reassign the tasks first."
                )

            subject_name = subject.name
            self._db.delete(subject)
            self._db.commit()
            
            logger.info(f"Deleted subject {subject_id}: {subject_name}")
            return True
            
        except ValueError as e:
            self._db.rollback()
            logger.warning(f"Validation error deleting subject {subject_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Integrity error deleting subject {subject_id}: {str(e)}")
            
            # Check for foreign key constraint
            error_msg = str(e.orig).lower()
            if 'foreign key' in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot delete subject because it has associated tasks"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Subject deletion failed due to data conflict"
                )
        except SQLAlchemyError as e:
            self._db.rollback()
            logger.error(f"Database error deleting subject {subject_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete subject"
            )
        except Exception as e:
            self._db.rollback()
            logger.error(f"Unexpected error deleting subject {subject_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )
