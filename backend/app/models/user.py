from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
from ..core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    _email = Column("email", Text, nullable=False, unique=True, index=True)
    password = Column(Text, nullable=False)
    display_name = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    google_access_token = Column(Text, nullable=True)
    google_refresh_token = Column(Text, nullable=True)
    google_token_expiry = Column(DateTime(timezone=True), nullable=True)

    user_settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    subjects = relationship("Subject", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")

    def __init__(
        self,
        email: str,
        password: str,
        display_name: str,
        google_access_token: str = None,
        google_refresh_token: str = None,
        google_token_expiry=None,
    ):
        if not email or "@" not in email:
            raise ValueError("Invalid email address")
        if not display_name or not display_name.strip():
            raise ValueError("display_name cannot be empty")
        self._email = email
        self.password = password
        self.display_name = display_name
        self.google_access_token = google_access_token
        self.google_refresh_token = google_refresh_token
        self.google_token_expiry = google_token_expiry

    @hybrid_property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str):
        if not value or "@" not in value:
            raise ValueError("Invalid email address")
        self._email = value

    @email.expression
    def email(cls):
        return cls._email

    def is_google_connected(self) -> bool:
        """Returns True if user has linked a Google account."""
        return self.google_access_token is not None

    def clear_google_tokens(self):
        """Removes all Google OAuth tokens, effectively disconnecting the account."""
        self.google_access_token = None
        self.google_refresh_token = None
        self.google_token_expiry = None


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True)
    chart_type = Column(Text, nullable=False, default="bar")
    _capacity = Column("capacity", Integer, nullable=False, default=8)
    density = Column(Text, nullable=False, default="medium")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="user_settings")

    def __init__(
        self,
        user_id: int,
        chart_type: str = "bar",
        capacity: int = 8,
        density: str = "medium",
    ):
        self.user_id = user_id
        self.chart_type = chart_type
        self.capacity = capacity  # goes through setter
        self.density = density

    @property
    def capacity(self) -> int:
        return self._capacity

    @capacity.setter
    def capacity(self, value: int):
        if value is not None and value <= 0:
            raise ValueError("capacity must be greater than 0")
        self._capacity = value

    def is_default(self) -> bool:
        """Returns True if all settings are still at their default values."""
        return self.chart_type == "bar" and self._capacity == 8 and self.density == "medium"

    def reset_to_default(self):
        """Resets all settings back to default values."""
        self.chart_type = "bar"
        self.capacity = 8
        self.density = "medium"
