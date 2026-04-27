from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..core.database import Base

class StatusEnum(enum.Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    FINISHED = "Finished"

class WorkTypeEnum(enum.Enum):
    DEEP = "Deep"
    FOCUS = "Focus"
    CHILL = "Chill"

class MainWork(Base):
    __tablename__ = "main_works"
    
    mainWork_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    note = Column(Text)
    deadLine = Column(DateTime(timezone=True))
    status = Column(Enum(StatusEnum), default=StatusEnum.PENDING)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    update_at = Column(DateTime(timezone=True), onupdate=func.now())
    create_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="main_works")
    sub_tasks = relationship("SubTask", back_populates="main_work", cascade="all, delete-orphan")

class SubTask(Base):
    __tablename__ = "sub_tasks"
    
    subTask_id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    work_type = Column(Enum(WorkTypeEnum), nullable=False)
    status = Column(Boolean, default=False)
    work_id = Column(Integer, ForeignKey("main_works.mainWork_id"), nullable=False)
    update_at = Column(DateTime(timezone=True), onupdate=func.now())
    create_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    main_work = relationship("MainWork", back_populates="sub_tasks")
