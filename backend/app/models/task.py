from datetime import date
from sqlalchemy import Column, Integer, Text, DateTime, Date, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
from ..core.database import Base

_VALID_STATUSES = {"pending", "in_progress", "done"}


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    title = Column(Text, nullable=True)
    deadline_date = Column(Date, nullable=True)
    difficulty = Column(Integer, nullable=True)
    importance = Column(Integer, nullable=True)
    comfortable = Column(Boolean, nullable=True)
    estimated_hours = Column(Numeric(4, 1), nullable=True)
    _status = Column("status", Text, nullable=False, default="pending")
    google_event_ids = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="tasks")
    subject = relationship("Subject", back_populates="tasks")
    task_slots = relationship("TaskSlot", back_populates="task", cascade="all, delete-orphan")

    def __init__(
        self,
        title: str = None,
        status: str = "pending",
        user_id: int = None,
        subject_id: int = None,
        deadline_date=None,
        difficulty: int = None,
        importance: int = None,
        comfortable: bool = None,
        estimated_hours=None,
        google_event_ids: str = None,
    ):
        if status not in _VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {_VALID_STATUSES}")
        self.title = title
        self._status = status
        self.user_id = user_id
        self.subject_id = subject_id
        self.deadline_date = deadline_date
        self.difficulty = difficulty
        self.importance = importance
        self.comfortable = comfortable
        self.estimated_hours = estimated_hours
        self.google_event_ids = google_event_ids

    @hybrid_property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str):
        if value not in _VALID_STATUSES:
            raise ValueError(f"Invalid status '{value}'. Must be one of: {_VALID_STATUSES}")
        self._status = value

    @status.expression
    def status(cls):
        return cls._status

    def is_overdue(self) -> bool:
        """Returns True if deadline has passed and task is not done."""
        if self.deadline_date is None or self._status == "done":
            return False
        return date.today() > self.deadline_date

    def priority_score(self) -> float:
        """Weighted score combining importance (60%) and difficulty (40%), range 0–10."""
        importance = self.importance or 0
        difficulty = self.difficulty or 0
        score = (importance * 0.6) + (difficulty * 0.4)
        if not (0 <= score <= 10):
            raise ValueError(f"priority_score out of range: {score}")
        return round(score, 2)


class TaskSlot(Base):
    __tablename__ = "task_slots"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    slot_date = Column(Date, nullable=True)
    start_hour = Column(Numeric(4, 2), nullable=True)
    _hours = Column("hours", Numeric(4, 1), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    task = relationship("Task", back_populates="task_slots")

    def __init__(self, task_id: int = None, slot_date=None, start_hour=None, hours=None):
        self.task_id = task_id
        self.slot_date = slot_date
        self.start_hour = start_hour
        self.hours = hours  # goes through setter

    @property
    def hours(self):
        return self._hours

    @hours.setter
    def hours(self, value):
        if value is not None and float(value) <= 0:
            raise ValueError("hours must be greater than 0")
        self._hours = value

    def duration_hours(self) -> float:
        """Returns slot duration as float."""
        return float(self._hours) if self._hours is not None else 0.0

    def end_hour(self) -> float:
        """Calculates end hour; raises if data is missing or exceeds 24:00."""
        if self.start_hour is None or self._hours is None:
            raise ValueError("start_hour and hours must be set to calculate end_hour")
        result = float(self.start_hour) + float(self._hours)
        if result > 24.0:
            raise ValueError(f"end_hour {result} exceeds 24:00")
        return result
