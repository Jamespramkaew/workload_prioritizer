from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    update_at = Column(DateTime(timezone=True), onupdate=func.now())
    create_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    main_works = relationship("MainWork", back_populates="user", cascade="all, delete-orphan")
