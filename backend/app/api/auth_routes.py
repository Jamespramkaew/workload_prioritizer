from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.schemas.user_schema import UserRegister, UserLogin, UserResponse
from app.services import auth as auth_service
from app.api.dependencies import get_current_user, COOKIE_NAME
from app.models.user import User


router = APIRouter(prefix="/auth", tags=["Authentication"])


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        secure=True,
        samesite="none",
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, response: Response, db: Session = Depends(get_db)):
    user = auth_service.register_user(
        db, payload.email, payload.password, payload.display_name
    )
    set_auth_cookie(response, create_access_token(user.id))
    return user


@router.post("/login", response_model=UserResponse)
def login(payload: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, payload.email, payload.password)
    set_auth_cookie(response, create_access_token(user.id))
    return user


@router.post("/logout")
def logout(response: Response, current_user: User = Depends(get_current_user)):
    clear_auth_cookie(response)
    return {"status": "logged out"}


@router.get("/verify", response_model=UserResponse)
def verify(current_user: User = Depends(get_current_user)):
    return current_user
