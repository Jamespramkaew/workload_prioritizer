from fastapi import HTTPException, Response, status
from sqlalchemy.orm import Session

from app.schemas.user_schema import UserResponse, UserSettingsResponse, UserSettingsUpdate
from app.models.user import User, UserSettings
from app.api.dependencies import COOKIE_NAME


class UserController:
    def __init__(self, db: Session):
        self._db = db

    def get_me(self, current_user: User) -> UserResponse:
        return current_user

    def get_my_settings(self, current_user: User) -> UserSettingsResponse:
        settings = self._db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
        if settings is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Settings not found")
        return settings

    def update_my_settings(self, current_user: User, body: UserSettingsUpdate) -> UserSettingsResponse:
        settings = self._db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
        if settings is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Settings not found")

        for field, value in body.model_dump(exclude_none=True).items():
            setattr(settings, field, value)

        self._db.commit()
        self._db.refresh(settings)
        return settings

    def delete_me(self, current_user: User, response: Response) -> dict:
        self._db.delete(current_user)
        self._db.commit()
        response.delete_cookie(key=COOKIE_NAME, path="/", secure=True, samesite="none")
        return {"status": "deleted", "email": current_user.email}

    def delete_all_users(self) -> dict:
        count = self._db.query(User).count()
        self._db.query(User).delete()
        self._db.commit()
        return {"status": "deleted", "count": count}
