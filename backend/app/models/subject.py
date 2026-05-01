from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
from ..core.database import Base


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    _name = Column("name", Text, nullable=True)
    short_name = Column(Text, nullable=True)
    color = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="subjects")
    tasks = relationship("Task", back_populates="subject", cascade="all, delete-orphan")

    def __init__(
        self,
        user_id: int = None,
        name: str = None,
        short_name: str = None,
        color: str = None,
        sort_order: int = 0,
    ):
        self.user_id = user_id
        self.name = name  # goes through setter
        self.short_name = short_name
        self.color = color
        self.sort_order = sort_order

    @hybrid_property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        if value is not None and len(value.strip()) == 0:
            raise ValueError("Subject name cannot be empty string")
        self._name = value

    @name.expression
    def name(cls):
        return cls._name

    def display_name(self) -> str:
        """Returns short_name if available, otherwise full name."""
        label = self.short_name or self._name
        if not label:
            raise ValueError("Subject has no name or short_name set")
        return label

    def pending_task_count(self) -> int:
        """Counts tasks that are not yet done."""
        return sum(1 for t in self.tasks if t.status != "done")
