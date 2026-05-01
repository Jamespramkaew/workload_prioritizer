"""
Test Task API endpoints with error handling
Tests all CRUD operations and edge cases
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, timedelta
from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.subject import Subject
from app.models.task import Task

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_tasks.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Setup and teardown for each test"""
    # Setup: Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create test user and subject
    db = TestingSessionLocal()
    test_user = User(id=1, username="testuser", email="test@example.com")
    test_subject = Subject(id=1, user_id=1, name="Mathematics", color="#FF6B6B")
    db.add(test_user)
    db.add(test_subject)
    db.commit()
    db.close()
    
    yield
    
    # Teardown: Drop all tables
    Base.metadata.drop_all(bind=engine)


class TestTaskAPI:
    """Test Task API endpoints"""
    
    def test_create_task_success(self):
        """Test creating a task successfully"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/tasks",
            json={
                "title": "Complete homework",
                "deadline_date": tomorrow.isoformat(),
                "difficulty": 3,
                "importance": 4,
                "comfortable": True,
                "estimated_hours": 5.5,
                "status": "pending",
                "user_id": 1,
                "subject_id": 1
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Complete homework"
        assert data["difficulty"] == 3
        assert data["importance"] == 4
        assert data["estimated_hours"] == 5.5
        assert "id" in data
        assert "created_at" in data
    
    def test_create_task_with_slots(self):
        """Test creating task with time slots"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/tasks",
            json={
                "title": "Study for exam",
                "deadline_date": tomorrow.isoformat(),
                "difficulty": 4,
                "importance": 5,
                "estimated_hours": 10.0,
                "status": "pending",
                "user_id": 1,
                "subject_id": 1,
                "slots": [
                    {
                        "slot_date": tomorrow.isoformat(),
                        "start_hour": 9.0,
                        "hours": 3.0
                    },
                    {
                        "slot_date": tomorrow.isoformat(),
                        "start_hour": 14.0,
                        "hours": 2.5
                    }
                ]
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["task_slots"]) == 2
        assert data["task_slots"][0]["hours"] == 3.0
        assert data["task_slots"][1]["hours"] == 2.5
    
    def test_create_task_empty_title(self):
        """Test creating task with empty title"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/tasks",
            json={
                "title": "",
                "deadline_date": tomorrow.isoformat(),
                "difficulty": 3,
                "importance": 3,
                "estimated_hours": 5.0,
                "user_id": 1
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_create_task_whitespace_title(self):
        """Test creating task with whitespace-only title"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/tasks",
            json={
                "title": "   ",
                "deadline_date": tomorrow.isoformat(),
                "difficulty": 3,
                "importance": 3,
                "estimated_hours": 5.0,
                "user_id": 1
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_create_task_invalid_difficulty(self):
        """Test creating task with invalid difficulty"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/tasks",
            json={
                "title": "Test task",
                "deadline_date": tomorrow.isoformat(),
                "difficulty": 6,  # Invalid: must be 1-5
                "importance": 3,
                "estimated_hours": 5.0,
                "user_id": 1
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_create_task_invalid_importance(self):
        """Test creating task with invalid importance"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/tasks",
            json={
                "title": "Test task",
                "deadline_date": tomorrow.isoformat(),
                "difficulty": 3,
                "importance": 0,  # Invalid: must be 1-5
                "estimated_hours": 5.0,
                "user_id": 1
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_create_task_negative_hours(self):
        """Test creating task with negative estimated hours"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/tasks",
            json={
                "title": "Test task",
                "deadline_date": tomorrow.isoformat(),
                "difficulty": 3,
                "importance": 3,
                "estimated_hours": -5.0,  # Invalid
                "user_id": 1
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_create_task_invalid_status(self):
        """Test creating task with invalid status"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/tasks",
            json={
                "title": "Test task",
                "deadline_date": tomorrow.isoformat(),
                "difficulty": 3,
                "importance": 3,
                "estimated_hours": 5.0,
                "status": "invalid_status",  # Invalid
                "user_id": 1
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_create_task_past_deadline(self):
        """Test creating task with deadline in far past"""
        far_past = date.today() - timedelta(days=400)
        response = client.post(
            "/api/tasks",
            json={
                "title": "Old task",
                "deadline_date": far_past.isoformat(),
                "difficulty": 3,
                "importance": 3,
                "estimated_hours": 5.0,
                "user_id": 1
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_create_task_invalid_subject_id(self):
        """Test creating task with non-existent subject"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/tasks",
            json={
                "title": "Test task",
                "deadline_date": tomorrow.isoformat(),
                "difficulty": 3,
                "importance": 3,
                "estimated_hours": 5.0,
                "user_id": 1,
                "subject_id": 99999  # Non-existent
            }
        )
        assert response.status_code == 400  # Bad request (foreign key)
    
    def test_create_task_slot_exceeds_24_hours(self):
        """Test creating task with slot that exceeds 24 hours"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/tasks",
            json={
                "title": "Test task",
                "deadline_date": tomorrow.isoformat(),
                "difficulty": 3,
                "importance": 3,
                "estimated_hours": 30.0,
                "user_id": 1,
                "slots": [
                    {
                        "slot_date": tomorrow.isoformat(),
                        "start_hour": 20.0,
                        "hours": 5.0  # 20 + 5 = 25 > 24
                    }
                ]
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_create_task_slots_exceed_estimated_hours(self):
        """Test creating task where total slot hours exceed estimated hours"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/tasks",
            json={
                "title": "Test task",
                "deadline_date": tomorrow.isoformat(),
                "difficulty": 3,
                "importance": 3,
                "estimated_hours": 5.0,
                "user_id": 1,
                "slots": [
                    {
                        "slot_date": tomorrow.isoformat(),
                        "start_hour": 9.0,
                        "hours": 3.0
                    },
                    {
                        "slot_date": tomorrow.isoformat(),
                        "start_hour": 14.0,
                        "hours": 3.0  # Total: 6 > 5
                    }
                ]
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_list_tasks_success(self):
        """Test listing tasks"""
        # Create test tasks
        tomorrow = date.today() + timedelta(days=1)
        client.post(
            "/api/tasks",
            json={
                "title": "Task 1",
                "deadline_date": tomorrow.isoformat(),
                "difficulty": 3,
                "importance": 4,
                "estimated_hours": 5.0,
                "status": "pending",
                "user_id": 1
            }
        )
        client.post(
            "/api/tasks",
            json={
                "title": "Task 2",
                "deadline_date": tomorrow.isoformat(),
                "difficulty": 2,
                "importance": 5,
                "estimated_hours": 3.0,
                "status": "in_progress",
                "user_id": 1
            }
        )
        
        response = client.get("/api/tasks?status=all")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
    
    def test_list_tasks_filter_by_status(self):
        """Test listing tasks filtered by status"""
        tomorrow = date.today() + timedelta(days=1)
        client.post(
            "/api/tasks",
            json={
                "title": "Pending task",
                "deadline_date": tomorrow.isoformat(),
                "difficulty": 3,
                "importance": 3,
                "estimated_hours": 5.0,
                "status": "pending",
                "user_id": 1
            }
        )
        
        response = client.get("/api/tasks?status=pending")
        assert response.status_code == 200
        data = response.json()
        assert all(task["status"] == "pending" for task in data)
    
    def test_list_tasks_invalid_status(self):
        """Test listing tasks with invalid status"""
        response = client.get("/api/tasks?status=invalid")
        assert response.status_code == 422  # Validation error
    
    def test_get_task_success(self):
        """Test getting a single task"""
        # Create task
        tomorrow = date.today() + timedelta(days=1)
        create_response = client.post(
            "/api/tasks",
            json={
                "title": "Get test task",
                "deadline_date": tomorrow.isoformat(),
                "difficulty": 3,
                "importance": 3,
                "estimated_hours": 5.0,
                "user_id": 1
            }
        )
        task_id = create_response.json()["id"]
        
        # Get task
        response = client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Get test task"
        assert data["id"] == task_id
    
    def test_get_task_not_found(self):
        """Test getting non-existent task"""
        response = client.get("/api/tasks/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_task_invalid_id(self):
        """Test getting task with invalid ID"""
        response = client.get("/api/tasks/0")
        assert response.status_code == 400  # Bad request
    
    def test_update_task_success(self):
        """Test updating a task"""
        # Create task
        tomorrow = date.today() + timedelta(days=1)
        create_response = client.post(
            "/api/tasks",
            json={
                "title": "Original title",
                "deadline_date": tomorrow.isoformat(),
                "difficulty": 3,
                "importance": 3,
                "estimated_hours": 5.0,
                "status": "pending",
                "user_id": 1
            }
        )
        task_id = create_response.json()["id"]
        
        # Update task
        response = client.patch(
            f"/api/tasks/{task_id}",
            json={
                "title": "Updated title",
                "status": "in_progress"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated title"
        assert data["status"] == "in_progress"
    
    def test_update_task_not_found(self):
        """Test updating non-existent task"""
        response = client.patch(
            "/api/tasks/99999",
            json={"title": "Updated"}
        )
        assert response.status_code == 404
    
    def test_update_task_empty_title(self):
        """Test updating task with empty title"""
        # Create task
        tomorrow = date.today() + timedelta(days=1)
        create_response = client.post(
            "/api/tasks",
            json={
                "title": "Original",
                "deadline_date": tomorrow.isoformat(),
                "difficulty": 3,
                "importance": 3,
                "estimated_hours": 5.0,
                "user_id": 1
            }
        )
        task_id = create_response.json()["id"]
        
        # Try to update with empty title
        response = client.patch(
            f"/api/tasks/{task_id}",
            json={"title": ""}
        )
        assert response.status_code == 422  # Validation error
    
    def test_update_task_invalid_status(self):
        """Test updating task with invalid status"""
        # Create task
        tomorrow = date.today() + timedelta(days=1)
        create_response = client.post(
            "/api/tasks",
            json={
                "title": "Test",
                "deadline_date": tomorrow.isoformat(),
                "difficulty": 3,
                "importance": 3,
                "estimated_hours": 5.0,
                "user_id": 1
            }
        )
        task_id = create_response.json()["id"]
        
        # Try to update with invalid status
        response = client.patch(
            f"/api/tasks/{task_id}",
            json={"status": "invalid"}
        )
        assert response.status_code == 422  # Validation error
    
    def test_delete_task_success(self):
        """Test deleting a task"""
        # Create task
        tomorrow = date.today() + timedelta(days=1)
        create_response = client.post(
            "/api/tasks",
            json={
                "title": "To be deleted",
                "deadline_date": tomorrow.isoformat(),
                "difficulty": 3,
                "importance": 3,
                "estimated_hours": 5.0,
                "user_id": 1
            }
        )
        task_id = create_response.json()["id"]
        
        # Delete task
        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 204
        
        # Verify deletion
        get_response = client.get(f"/api/tasks/{task_id}")
        assert get_response.status_code == 404
    
    def test_delete_task_not_found(self):
        """Test deleting non-existent task"""
        response = client.delete("/api/tasks/99999")
        assert response.status_code == 404
    
    def test_delete_task_invalid_id(self):
        """Test deleting task with invalid ID"""
        response = client.delete("/api/tasks/0")
        assert response.status_code == 400
    
    def test_task_title_trimming(self):
        """Test that task titles are trimmed"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/tasks",
            json={
                "title": "  Trimmed Title  ",
                "deadline_date": tomorrow.isoformat(),
                "difficulty": 3,
                "importance": 3,
                "estimated_hours": 5.0,
                "user_id": 1
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Trimmed Title"  # Should be trimmed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
