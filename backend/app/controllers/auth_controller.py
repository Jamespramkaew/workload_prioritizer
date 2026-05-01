import logging
from fastapi import Response, HTTPException, status
from sqlalchemy.orm import Session
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)

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
        try:
            user = auth_service.register_user(self._db, payload.email, payload.password, payload.display_name)
            self._set_cookie(response, create_access_token(user.id))
            logger.info(f"User registered and authenticated: {payload.email}")
            return user
        except HTTPException:
            raise
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Register error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register user"
            )

    def login(self, payload: UserLogin, response: Response) -> UserResponse:
        try:
            user = auth_service.authenticate_user(self._db, payload.email, payload.password)
            self._set_cookie(response, create_access_token(user.id))
            logger.info(f"User logged in successfully: {payload.email}")
            return user
        except HTTPException:
            raise
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to authenticate user"
            )

    def logout(self, response: Response) -> dict:
        self._clear_cookie(response)
        return {"status": "logged out"}

    def verify(self, current_user: User) -> UserResponse:
        return current_user
