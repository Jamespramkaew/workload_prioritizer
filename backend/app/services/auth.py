import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, UserSettings
from app.core.security import hash_password, verify_password
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


def register_user(db: Session, email: str, password: str, display_name: str) -> User:
    try:
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        
        logger.info(f"Registering user: email={email}, display_name={display_name}")

        user = User(
            email=email,
            password=hash_password(password),
            display_name=display_name,
        )
        db.add(user)
        db.flush()
        db.add(UserSettings(user_id=user.id))
        db.commit()
        db.refresh(user)
        logger.info(f"User registered successfully: {email}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Database error during registration: {str(e)}")
        raise DatabaseError(f"Failed to register user: {str(e)}")


def authenticate_user(db: Session, email: str, password: str) -> User:
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        logger.info(f"User authenticated successfully: {email}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error during authentication: {str(e)}")
        raise DatabaseError(f"Failed to authenticate user: {str(e)}")
