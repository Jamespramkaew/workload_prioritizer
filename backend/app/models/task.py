from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    title = Column(Text, nullable=True)
    deadline_date = Column(Date, nullable=True)
    difficulty = Column(Integer, nullable=True)  # SMALLINT
    importance = Column(Integer, nullable=True)  # SMALLINT
    comfortable = Column(Boolean, nullable=True)
    estimated_hours = Column(Numeric(4, 1), nullable=True)
    status = Column(Text, nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    subject = relationship("Subject", back_populates="tasks")
    task_slots = relationship("TaskSlot", back_populates="task", cascade="all, delete-orphan")


class TaskSlot(Base):
    __tablename__ = "task_slots"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    slot_date = Column(Date, nullable=True)
    start_hour = Column(Numeric(4, 2), nullable=True)
    hours = Column(Numeric(4, 1), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    task = relationship("Task", back_populates="task_slots")
