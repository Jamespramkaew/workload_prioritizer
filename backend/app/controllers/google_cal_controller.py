import logging
from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.models.user import User
from app.models.task import Task
from app.services.google_cal import GoogleCalendarService

FRONTEND_URL = "http://localhost:3000"


class GoogleCalController:
    def __init__(self, db: Session):
        self._db = db

    def google_login(self, current_user) -> RedirectResponse:
        try:
            url = GoogleCalendarService.get_oauth_url(str(current_user.id))
            logger.info(f"Google login initiated for user {current_user.id}")
            return RedirectResponse(url)
        except Exception as e:
            logger.error(f"Google login controller error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initiate Google login"
            )

    def google_callback(self, code: str, state: str) -> RedirectResponse:
        try:
            user_id, tokens = GoogleCalendarService.exchange_code(code, state)
            user = self._db.query(User).filter(User.id == int(user_id)).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            user.google_access_token = tokens["access_token"]
            user.google_refresh_token = tokens["refresh_token"]
            user.google_token_expiry = tokens["expiry"]
            self._db.commit()
            logger.info(f"Google callback processed for user {user_id}")
            return RedirectResponse(url=FRONTEND_URL)
        except HTTPException:
            raise
        except Exception as e:
            self._db.rollback()
            logger.error(f"Google callback controller error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process Google callback"
            )

    def sync_task(self, task_id: int, current_user: User) -> dict:
        try:
            if not current_user.google_access_token:
                raise HTTPException(status_code=400, detail="Google Calendar not connected. Go to /auth/google/login first.")

            task = self._db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
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
            self._db.commit()
            logger.info(f"Task {task_id} synced to Google Calendar ({len(event_ids)} events)")
            return {"status": "synced", "event_count": len(event_ids)}
        except HTTPException:
            raise
        except Exception as e:
            self._db.rollback()
            logger.error(f"Sync task controller error for task {task_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to sync task to Google Calendar"
            )

    def unsync_task(self, task_id: int, current_user: User) -> dict:
        try:
            if not current_user.google_access_token:
                raise HTTPException(status_code=400, detail="Google Calendar not connected")

            task = self._db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")

            if task.google_event_ids:
                GoogleCalendarService(
                    current_user.google_access_token,
                    current_user.google_refresh_token,
                    current_user.google_token_expiry,
                ).delete_events(task.google_event_ids.split(","))
                task.google_event_ids = None
                self._db.commit()
            logger.info(f"Task {task_id} unsynced from Google Calendar")
            return {"status": "unsynced"}
        except HTTPException:
            raise
        except Exception as e:
            self._db.rollback()
            logger.error(f"Unsync task controller error for task {task_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to unsync task from Google Calendar"
            )
