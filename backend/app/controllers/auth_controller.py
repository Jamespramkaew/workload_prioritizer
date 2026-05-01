from fastapi import Response
from sqlalchemy.orm import Session

from app.core.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.schemas.user_schema import UserRegister, UserLogin, UserResponse
from app.services import auth as auth_service
from app.api.dependencies import COOKIE_NAME
from app.models.user import User


class AuthController:
    def __init__(self, db: Session):
        self._db = db

    def _set_cookie(self, response: Response, token: str) -> None:
        response.set_cookie(
            key=COOKIE_NAME,
            value=token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            path="/",
        )

    def _clear_cookie(self, response: Response) -> None:
        response.delete_cookie(key=COOKIE_NAME, path="/", secure=True, samesite="none")

    def register(self, payload: UserRegister, response: Response) -> UserResponse:
        user = auth_service.register_user(self._db, payload.email, payload.password, payload.display_name)
        self._set_cookie(response, create_access_token(user.id))
        return user

    def login(self, payload: UserLogin, response: Response) -> UserResponse:
        user = auth_service.authenticate_user(self._db, payload.email, payload.password)
        self._set_cookie(response, create_access_token(user.id))
        return user

    def logout(self, response: Response) -> dict:
        self._clear_cookie(response)
        return {"status": "logged out"}

    def verify(self, current_user: User) -> UserResponse:
        return current_user
