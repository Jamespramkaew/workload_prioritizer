"""
Test Subject API endpoints with error handling
Tests all CRUD operations and edge cases
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.subject import Subject

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_subjects.db"
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
    
    # Create test user
    db = TestingSessionLocal()
    test_user = User(id=1, username="testuser", email="test@example.com")
    db.add(test_user)
    db.commit()
    db.close()
    
    yield
    
    # Teardown: Drop all tables
    Base.metadata.drop_all(bind=engine)


class TestSubjectAPI:
    """Test Subject API endpoints"""
    
    def test_create_subject_success(self):
        """Test creating a subject successfully"""
        response = client.post(
            "/api/subjects",
            json={
                "name": "Mathematics",
                "short_name": "MATH",
                "color": "#FF6B6B",
                "sort_order": 1,
                "user_id": 1
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Mathematics"
        assert data["short_name"] == "MATH"
        assert data["color"] == "#FF6B6B"
        assert data["sort_order"] == 1
        assert "id" in data
        assert "created_at" in data
    
    def test_create_subject_minimal_data(self):
        """Test creating subject with only required fields"""
        response = client.post(
            "/api/subjects",
            json={
                "name": "Physics",
                "user_id": 1
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Physics"
        assert data["sort_order"] == 0  # default value
    
    def test_create_subject_empty_name(self):
        """Test creating subject with empty name"""
        response = client.post(
            "/api/subjects",
            json={
                "name": "",
                "user_id": 1
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_create_subject_whitespace_name(self):
        """Test creating subject with whitespace-only name"""
        response = client.post(
            "/api/subjects",
            json={
                "name": "   ",
                "user_id": 1
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_create_subject_invalid_color(self):
        """Test creating subject with invalid color format"""
        response = client.post(
            "/api/subjects",
            json={
                "name": "Chemistry",
                "color": "red",  # Invalid format
                "user_id": 1
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_create_subject_negative_sort_order(self):
        """Test creating subject with negative sort order"""
        response = client.post(
            "/api/subjects",
            json={
                "name": "Biology",
                "sort_order": -1,
                "user_id": 1
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_create_subject_duplicate_name(self):
        """Test creating subject with duplicate name"""
        # Create first subject
        client.post(
            "/api/subjects",
            json={
                "name": "English",
                "user_id": 1
            }
        )
        
        # Try to create duplicate
        response = client.post(
            "/api/subjects",
            json={
                "name": "English",
                "user_id": 1
            }
        )
        assert response.status_code == 400  # Bad request
        assert "already exists" in response.json()["detail"].lower()
    
    def test_list_subjects_success(self):
        """Test listing subjects"""
        # Create test subjects
        client.post("/api/subjects", json={"name": "Math", "user_id": 1, "sort_order": 2})
        client.post("/api/subjects", json={"name": "Science", "user_id": 1, "sort_order": 1})
        
        response = client.get("/api/subjects?user_id=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Should be sorted by sort_order
        assert data[0]["name"] == "Science"
        assert data[1]["name"] == "Math"
    
    def test_list_subjects_invalid_user_id(self):
        """Test listing subjects with invalid user ID"""
        response = client.get("/api/subjects?user_id=0")
        assert response.status_code == 422  # Validation error
    
    def test_list_subjects_negative_user_id(self):
        """Test listing subjects with negative user ID"""
        response = client.get("/api/subjects?user_id=-1")
        assert response.status_code == 422  # Validation error
    
    def test_get_subject_success(self):
        """Test getting a single subject"""
        # Create subject
        create_response = client.post(
            "/api/subjects",
            json={"name": "History", "user_id": 1}
        )
        subject_id = create_response.json()["id"]
        
        # Get subject
        response = client.get(f"/api/subjects/{subject_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "History"
        assert data["id"] == subject_id
    
    def test_get_subject_not_found(self):
        """Test getting non-existent subject"""
        response = client.get("/api/subjects/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_subject_invalid_id(self):
        """Test getting subject with invalid ID"""
        response = client.get("/api/subjects/0")
        assert response.status_code == 400  # Bad request
    
    def test_update_subject_success(self):
        """Test updating a subject"""
        # Create subject
        create_response = client.post(
            "/api/subjects",
            json={"name": "Geography", "user_id": 1}
        )
        subject_id = create_response.json()["id"]
        
        # Update subject
        response = client.patch(
            f"/api/subjects/{subject_id}",
            json={
                "name": "Advanced Geography",
                "color": "#00FF00"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Advanced Geography"
        assert data["color"] == "#00FF00"
    
    def test_update_subject_not_found(self):
        """Test updating non-existent subject"""
        response = client.patch(
            "/api/subjects/99999",
            json={"name": "Updated Name"}
        )
        assert response.status_code == 404
    
    def test_update_subject_empty_name(self):
        """Test updating subject with empty name"""
        # Create subject
        create_response = client.post(
            "/api/subjects",
            json={"name": "Art", "user_id": 1}
        )
        subject_id = create_response.json()["id"]
        
        # Try to update with empty name
        response = client.patch(
            f"/api/subjects/{subject_id}",
            json={"name": ""}
        )
        assert response.status_code == 422  # Validation error
    
    def test_update_subject_duplicate_name(self):
        """Test updating subject to duplicate name"""
        # Create two subjects
        client.post("/api/subjects", json={"name": "Music", "user_id": 1})
        create_response = client.post("/api/subjects", json={"name": "Drama", "user_id": 1})
        subject_id = create_response.json()["id"]
        
        # Try to update Drama to Music (duplicate)
        response = client.patch(
            f"/api/subjects/{subject_id}",
            json={"name": "Music"}
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
    
    def test_delete_subject_success(self):
        """Test deleting a subject"""
        # Create subject
        create_response = client.post(
            "/api/subjects",
            json={"name": "PE", "user_id": 1}
        )
        subject_id = create_response.json()["id"]
        
        # Delete subject
        response = client.delete(f"/api/subjects/{subject_id}")
        assert response.status_code == 204
        
        # Verify deletion
        get_response = client.get(f"/api/subjects/{subject_id}")
        assert get_response.status_code == 404
    
    def test_delete_subject_not_found(self):
        """Test deleting non-existent subject"""
        response = client.delete("/api/subjects/99999")
        assert response.status_code == 404
    
    def test_delete_subject_invalid_id(self):
        """Test deleting subject with invalid ID"""
        response = client.delete("/api/subjects/0")
        assert response.status_code == 400
    
    def test_subject_name_trimming(self):
        """Test that subject names are trimmed"""
        response = client.post(
            "/api/subjects",
            json={
                "name": "  Computer Science  ",
                "user_id": 1
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Computer Science"  # Should be trimmed
    
    def test_subject_color_uppercase(self):
        """Test that color codes are converted to uppercase"""
        response = client.post(
            "/api/subjects",
            json={
                "name": "Design",
                "color": "#abc123",
                "user_id": 1
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["color"] == "#ABC123"  # Should be uppercase


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
