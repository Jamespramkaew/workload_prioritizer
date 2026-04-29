from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, UserSettings
from app.core.security import hash_password, verify_password


def register_user(db: Session, email: str, password: str, display_name: str) -> User:
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    
    print(f"Registering user: email={email}, display_name={display_name}", flush=True)


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
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return user
