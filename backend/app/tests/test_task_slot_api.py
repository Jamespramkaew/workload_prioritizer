"""
Test Task Slot API endpoints with error handling
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
from app.models.task import Task, TaskSlot

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_task_slots.db"
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
    
    # Create test data
    db = TestingSessionLocal()
    test_user = User(id=1, username="testuser", email="test@example.com")
    test_subject = Subject(id=1, user_id=1, name="Mathematics", color="#FF6B6B")
    db.add(test_user)
    db.add(test_subject)
    db.commit()
    
    # Create test task
    tomorrow = date.today() + timedelta(days=1)
    test_task = Task(
        id=1,
        user_id=1,
        subject_id=1,
        title="Test Task",
        deadline_date=tomorrow,
        difficulty=3,
        importance=3,
        estimated_hours=10.0,
        status="pending"
    )
    db.add(test_task)
    db.commit()
    
    # Create initial slot
    initial_slot = TaskSlot(
        task_id=1,
        slot_date=tomorrow,
        start_hour=9.0,
        hours=3.0
    )
    db.add(initial_slot)
    db.commit()
    db.close()
    
    yield
    
    # Teardown: Drop all tables
    Base.metadata.drop_all(bind=engine)


class TestTaskSlotAPI:
    """Test Task Slot API endpoints"""
    
    def test_create_slot_success(self):
        """Test creating a slot successfully"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/tasks/1/slots",
            json={
                "slot_date": tomorrow.isoformat(),
                "start_hour": 14.0,
                "hours": 2.5
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["slot_date"] == tomorrow.isoformat()
        assert data["start_hour"] == 14.0
        assert data["hours"] == 2.5
        assert data["task_id"] == 1
        assert "id" in data
    
    def test_create_slot_invalid_task_id(self):
        """Test creating slot for non-existent task"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/tasks/99999/slots",
            json={
                "slot_date": tomorrow.isoformat(),
                "start_hour": 14.0,
                "hours": 2.5
            }
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_create_slot_negative_hours(self):
        """Test creating slot with negative hours"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/tasks/1/slots",
            json={
                "slot_date": tomorrow.isoformat(),
                "start_hour": 14.0,
                "hours": -2.0  # Invalid
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_create_slot_zero_hours(self):
        """Test creating slot with zero hours"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/tasks/1/slots",
            json={
                "slot_date": tomorrow.isoformat(),
                "start_hour": 14.0,
                "hours": 0.0  # Invalid
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_create_slot_invalid_start_hour(self):
        """Test creating slot with invalid start hour"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/tasks/1/slots",
            json={
                "slot_date": tomorrow.isoformat(),
                "start_hour": 25.0,  # Invalid: > 24
                "hours": 2.0
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_create_slot_negative_start_hour(self):
        """Test creating slot with negative start hour"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/tasks/1/slots",
            json={
                "slot_date": tomorrow.isoformat(),
                "start_hour": -1.0,  # Invalid
                "hours": 2.0
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_create_slot_exceeds_24_hours(self):
        """Test creating slot that exceeds 24 hours"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/tasks/1/slots",
            json={
                "slot_date": tomorrow.isoformat(),
                "start_hour": 22.0,
                "hours": 3.0  # 22 + 3 = 25 > 24
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_create_slot_exceeds_estimated_hours(self):
        """Test creating slot that would exceed estimated hours"""
        tomorrow = date.today() + timedelta(days=1)
        # Task has 10h estimated, already has 3h slot
        # Adding 8h would exceed (3 + 8 = 11 > 10)
        response = client.post(
            "/api/tasks/1/slots",
            json={
                "slot_date": tomorrow.isoformat(),
                "start_hour": 14.0,
                "hours": 8.0
            }
        )
        assert response.status_code == 400  # Bad request
        assert "exceed" in response.json()["detail"].lower()
    
    def test_update_slot_success(self):
        """Test updating a slot successfully"""
        # Get existing slot
        db = TestingSessionLocal()
        slot = db.query(TaskSlot).filter(TaskSlot.task_id == 1).first()
        slot_id = slot.id
        db.close()
        
        tomorrow = date.today() + timedelta(days=1)
        response = client.patch(
            f"/api/tasks/1/slots/{slot_id}",
            json={
                "start_hour": 10.0,
                "hours": 4.0
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["start_hour"] == 10.0
        assert data["hours"] == 4.0
    
    def test_update_slot_not_found(self):
        """Test updating non-existent slot"""
        response = client.patch(
            "/api/tasks/1/slots/99999",
            json={
                "start_hour": 10.0
            }
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_slot_wrong_task(self):
        """Test updating slot with wrong task ID"""
        # Get existing slot
        db = TestingSessionLocal()
        slot = db.query(TaskSlot).filter(TaskSlot.task_id == 1).first()
        slot_id = slot.id
        db.close()
        
        response = client.patch(
            f"/api/tasks/99999/slots/{slot_id}",
            json={
                "start_hour": 10.0
            }
        )
        assert response.status_code == 404
    
    def test_update_slot_negative_hours(self):
        """Test updating slot with negative hours"""
        # Get existing slot
        db = TestingSessionLocal()
        slot = db.query(TaskSlot).filter(TaskSlot.task_id == 1).first()
        slot_id = slot.id
        db.close()
        
        response = client.patch(
            f"/api/tasks/1/slots/{slot_id}",
            json={
                "hours": -2.0  # Invalid
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_update_slot_exceeds_24_hours(self):
        """Test updating slot to exceed 24 hours"""
        # Get existing slot
        db = TestingSessionLocal()
        slot = db.query(TaskSlot).filter(TaskSlot.task_id == 1).first()
        slot_id = slot.id
        db.close()
        
        response = client.patch(
            f"/api/tasks/1/slots/{slot_id}",
            json={
                "start_hour": 22.0,
                "hours": 3.0  # 22 + 3 = 25 > 24
            }
        )
        assert response.status_code == 400  # Bad request
        assert "exceed" in response.json()["detail"].lower()
    
    def test_update_slot_exceeds_estimated_hours(self):
        """Test updating slot to exceed estimated hours"""
        # Get existing slot
        db = TestingSessionLocal()
        slot = db.query(TaskSlot).filter(TaskSlot.task_id == 1).first()
        slot_id = slot.id
        db.close()
        
        # Update to 11 hours (exceeds 10h estimated)
        response = client.patch(
            f"/api/tasks/1/slots/{slot_id}",
            json={
                "hours": 11.0
            }
        )
        assert response.status_code == 400  # Bad request
        assert "exceed" in response.json()["detail"].lower()
    
    def test_delete_slot_success(self):
        """Test deleting a slot successfully"""
        # Create additional slot first (so we can delete one)
        tomorrow = date.today() + timedelta(days=1)
        create_response = client.post(
            "/api/tasks/1/slots",
            json={
                "slot_date": tomorrow.isoformat(),
                "start_hour": 14.0,
                "hours": 2.0
            }
        )
        new_slot_id = create_response.json()["id"]
        
        # Delete the new slot
        response = client.delete(f"/api/tasks/1/slots/{new_slot_id}")
        assert response.status_code == 204
        
        # Verify deletion
        db = TestingSessionLocal()
        slot = db.query(TaskSlot).filter(TaskSlot.id == new_slot_id).first()
        assert slot is None
        db.close()
    
    def test_delete_last_slot(self):
        """Test deleting the last slot (should fail)"""
        # Get the only existing slot
        db = TestingSessionLocal()
        slot = db.query(TaskSlot).filter(TaskSlot.task_id == 1).first()
        slot_id = slot.id
        db.close()
        
        # Try to delete it
        response = client.delete(f"/api/tasks/1/slots/{slot_id}")
        assert response.status_code == 400  # Bad request
        assert "last slot" in response.json()["detail"].lower()
    
    def test_delete_slot_not_found(self):
        """Test deleting non-existent slot"""
        response = client.delete("/api/tasks/1/slots/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_delete_slot_wrong_task(self):
        """Test deleting slot with wrong task ID"""
        # Get existing slot
        db = TestingSessionLocal()
        slot = db.query(TaskSlot).filter(TaskSlot.task_id == 1).first()
        slot_id = slot.id
        db.close()
        
        response = client.delete(f"/api/tasks/99999/slots/{slot_id}")
        assert response.status_code == 404
    
    def test_delete_slot_invalid_task_id(self):
        """Test deleting slot with invalid task ID"""
        response = client.delete("/api/tasks/0/slots/1")
        assert response.status_code == 400  # Bad request
    
    def test_delete_slot_invalid_slot_id(self):
        """Test deleting slot with invalid slot ID"""
        response = client.delete("/api/tasks/1/slots/0")
        assert response.status_code == 400  # Bad request
    
    def test_create_multiple_slots(self):
        """Test creating multiple slots for same task"""
        tomorrow = date.today() + timedelta(days=1)
        
        # Create first additional slot
        response1 = client.post(
            "/api/tasks/1/slots",
            json={
                "slot_date": tomorrow.isoformat(),
                "start_hour": 14.0,
                "hours": 2.0
            }
        )
        assert response1.status_code == 201
        
        # Create second additional slot
        response2 = client.post(
            "/api/tasks/1/slots",
            json={
                "slot_date": tomorrow.isoformat(),
                "start_hour": 17.0,
                "hours": 2.0
            }
        )
        assert response2.status_code == 201
        
        # Verify total slots
        db = TestingSessionLocal()
        total_slots = db.query(TaskSlot).filter(TaskSlot.task_id == 1).count()
        assert total_slots == 3  # Initial + 2 new
        db.close()
    
    def test_slot_time_precision(self):
        """Test slot time with decimal precision"""
        tomorrow = date.today() + timedelta(days=1)
        response = client.post(
            "/api/tasks/1/slots",
            json={
                "slot_date": tomorrow.isoformat(),
                "start_hour": 9.5,  # 9:30 AM
                "hours": 1.5  # 1.5 hours
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["start_hour"] == 9.5
        assert data["hours"] == 1.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
