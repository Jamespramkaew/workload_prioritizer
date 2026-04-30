from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from app.core.config import settings

FRONTEND_URL = "http://localhost:3000"
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.task import Task
from app.services import google_cal

router = APIRouter(tags=["Google Calendar"])


@router.get("/auth/google/login")
def google_login(current_user: User = Depends(get_current_user)):
    url = google_cal.get_oauth_url(str(current_user.id))
    return RedirectResponse(url)


@router.get("/auth/google/callback")
def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    user_id, tokens = google_cal.exchange_code(code, state)
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.google_access_token = tokens["access_token"]
    user.google_refresh_token = tokens["refresh_token"]
    user.google_token_expiry = tokens["expiry"]
    db.commit()
    return RedirectResponse(url=FRONTEND_URL)


@router.post("/api/tasks/{task_id}/sync-calendar", status_code=status.HTTP_200_OK)
def sync_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.google_access_token:
        raise HTTPException(status_code=400, detail="Google Calendar not connected. Go to /auth/google/login first.")

    task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not task.task_slots:
        raise HTTPException(status_code=400, detail="Task has no slots to sync")

    # ลบ events เก่าก่อน (ถ้ามี)
    if task.google_event_ids:
        google_cal.delete_events(
            current_user.google_access_token,
            current_user.google_refresh_token,
            current_user.google_token_expiry,
            task.google_event_ids.split(","),
        )

    event_ids = google_cal.create_events(
        current_user.google_access_token,
        current_user.google_refresh_token,
        current_user.google_token_expiry,
        task,
        task.task_slots,
    )
    task.google_event_ids = ",".join(event_ids)
    db.commit()
    return {"status": "synced", "event_count": len(event_ids)}


@router.delete("/api/tasks/{task_id}/sync-calendar", status_code=status.HTTP_200_OK)
def unsync_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.google_access_token:
        raise HTTPException(status_code=400, detail="Google Calendar not connected")

    task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.google_event_ids:
        google_cal.delete_events(
            current_user.google_access_token,
            current_user.google_refresh_token,
            current_user.google_token_expiry,
            task.google_event_ids.split(","),
        )
        task.google_event_ids = None
        db.commit()

    return {"status": "unsynced"}
