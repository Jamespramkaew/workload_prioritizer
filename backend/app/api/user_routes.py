from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from sqlalchemy.orm import Session
from app.schemas.user_schema import UserResponse, UserSettingsResponse, UserSettingsUpdate
from app.api.dependencies import get_current_user, COOKIE_NAME
from app.core.database import get_db
from app.models.user import User, UserSettings
from app.middleware.rate_limit import limiter, RateLimits

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
@limiter.limit(RateLimits.READ)
def get_me(request: Request, current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/me/settings", response_model=UserSettingsResponse)
@limiter.limit(RateLimits.READ)
def get_my_settings(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if settings is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Settings not found")
    return settings


@router.patch("/me/settings", response_model=UserSettingsResponse)
@limiter.limit(RateLimits.UPDATE)
def update_my_settings(
    request: Request,
    body: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if settings is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Settings not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(settings, field, value)

    db.commit()
    db.refresh(settings)
    return settings


@router.delete("/me", status_code=status.HTTP_200_OK, tags=["debug"])
@limiter.limit(RateLimits.DELETE)
def delete_me(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.delete(current_user)
    db.commit()
    response.delete_cookie(key=COOKIE_NAME, path="/", secure=True, samesite="none")
    return {"status": "deleted", "email": current_user.email}


@router.delete("/all", status_code=status.HTTP_200_OK, tags=["debug"])
@limiter.limit(RateLimits.DELETE)
def delete_all_users(request: Request, db: Session = Depends(get_db)):
    """[DEBUG] Delete all users and their related data"""
    count = db.query(User).count()
    db.query(User).delete()
    db.commit()
    return {"status": "deleted", "count": count}
