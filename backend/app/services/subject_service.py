from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.subject import Subject
from app.schemas.subject_schema import SubjectCreate, SubjectUpdate


class SubjectService:
    
    @staticmethod
    def list_subjects(db: Session, user_id: int) -> List[Subject]:
        """List all subjects for a specific user"""
        return db.query(Subject).filter(
            Subject.user_id == user_id
        ).order_by(Subject.sort_order, Subject.name).all()
    
    @staticmethod
    def get_subject(db: Session, subject_id: int) -> Optional[Subject]:
        """Get a single subject by ID"""
        return db.query(Subject).filter(Subject.id == subject_id).first()
    
    @staticmethod
    def create_subject(db: Session, subject_data: SubjectCreate) -> Subject:
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
    
    @staticmethod
    def update_subject(db: Session, subject_id: int, subject_data: SubjectUpdate) -> Optional[Subject]:
        """Update a subject"""
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            return None
        
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
    
    @staticmethod
    def delete_subject(db: Session, subject_id: int) -> bool:
        """Delete a subject"""
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            return False
        
        db.delete(subject)
        db.commit()
        return True