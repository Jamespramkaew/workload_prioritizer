from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)

FRONTEND_URL = "https://workload-prioritizer.vercel.app"
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.task import Task
from app.services.google_cal import GoogleCalendarService
from app.middleware.rate_limit import limiter, RateLimits

router = APIRouter(tags=["Google Calendar"])


@router.get("/auth/google/login")
@limiter.limit(RateLimits.AUTH_LOGIN)
def google_login(request: Request, current_user: User = Depends(get_current_user)):
    url = GoogleCalendarService.get_oauth_url(str(current_user.id))
    return RedirectResponse(url)


@router.get("/auth/google/callback")
@limiter.limit(RateLimits.AUTH_REFRESH)
def google_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    try:
        user_id, tokens = GoogleCalendarService.exchange_code(code, state)
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.google_access_token = tokens["access_token"]
        user.google_refresh_token = tokens["refresh_token"]
        user.google_token_expiry = tokens["expiry"]
        db.commit()
        logger.info(f"Google OAuth callback successful for user {user_id}")
        return RedirectResponse(url=FRONTEND_URL)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Google callback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process Google callback"
        )


@router.post("/api/tasks/{task_id}/sync-calendar", status_code=status.HTTP_200_OK)
@limiter.limit(RateLimits.GOOGLE_CALENDAR)
def sync_task(
    request: Request,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        if not current_user.google_access_token:
            raise HTTPException(status_code=400, detail="Google Calendar not connected. Go to /auth/google/login first.")

        task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if not task.task_slots:
            raise HTTPException(status_code=400, detail="Task has no slots to sync")

        cal_service = GoogleCalendarService(
            current_user.google_access_token,
            current_user.google_refresh_token,
            current_user.google_token_expiry,
        )

        if task.google_event_ids:
            cal_service.delete_events(task.google_event_ids.split(","))

        event_ids = cal_service.create_events(task, task.task_slots)
        task.google_event_ids = ",".join(event_ids)
        db.commit()
        logger.info(f"Task {task_id} synced to Google Calendar ({len(event_ids)} events) by user {current_user.id}")
        return {"status": "synced", "event_count": len(event_ids)}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Sync task error for task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync task to Google Calendar"
        )


@router.delete("/api/tasks/{task_id}/sync-calendar", status_code=status.HTTP_200_OK)
@limiter.limit(RateLimits.GOOGLE_CALENDAR)
def unsync_task(
    request: Request,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        if not current_user.google_access_token:
            raise HTTPException(status_code=400, detail="Google Calendar not connected")

        task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.google_event_ids:
            GoogleCalendarService(
                current_user.google_access_token,
                current_user.google_refresh_token,
                current_user.google_token_expiry,
            ).delete_events(task.google_event_ids.split(","))
            task.google_event_ids = None
            db.commit()
        logger.info(f"Task {task_id} unsynced from Google Calendar by user {current_user.id}")
        return {"status": "unsynced"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unsync task error for task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unsync task from Google Calendar"
        )
