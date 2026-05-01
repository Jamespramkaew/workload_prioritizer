from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.subject import Subject
from app.schemas.subject_schema import SubjectCreate, SubjectUpdate


class SubjectService:
    def __init__(self, db: Session):
        self._db = db

    @property
    def db(self) -> Session:
        return self._db

    def list_subjects(self, user_id: int) -> List[Subject]:
        return self._db.query(Subject).filter(
            Subject.user_id == user_id
        ).order_by(Subject.sort_order, Subject.name).all()

    def get_subject(self, subject_id: int) -> Optional[Subject]:
        return self._db.query(Subject).filter(Subject.id == subject_id).first()

    def create_subject(self, subject_data: SubjectCreate) -> Subject:
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
        return subject

    def update_subject(self, subject_id: int, subject_data: SubjectUpdate) -> Optional[Subject]:
        subject = self._db.query(Subject).filter(Subject.id == subject_id).first()
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

        self._db.commit()
        self._db.refresh(subject)
        return subject

    def delete_subject(self, subject_id: int) -> bool:
        subject = self._db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            return False

        self._db.delete(subject)
        self._db.commit()
        return True
