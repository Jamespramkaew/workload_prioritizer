"""
Test Input Validation
Tests for Pydantic schema validation
"""
import pytest
from pydantic import ValidationError
from datetime import date, timedelta

from app.schemas.task_schema import TaskCreate, TaskSlotCreate, TaskUpdate
from app.schemas.subject_schema import SubjectCreate, SubjectUpdate
from app.schemas.user_schema import UserRegister, UserSettingsUpdate


class TestTaskValidation:
    """Test Task schema validation"""
    
    def test_valid_task_creation(self):
        """Test creating a valid task"""
        task = TaskCreate(
            title="Complete Assignment",
            deadline_date=date.today() + timedelta(days=7),
            difficulty=3,
            importance=4,
            estimated_hours=5.0
        )
        assert task.title == "Complete Assignment"
        assert task.difficulty == 3
        assert task.importance == 4
    
    def test_difficulty_out_of_range(self):
        """Test difficulty validation"""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(
                title="Test",
                deadline_date=date.today(),
                difficulty=10,  # Invalid: > 5
                importance=3,
                estimated_hours=5.0
            )
        assert "difficulty" in str(exc_info.value).lower()
    
    def test_importance_out_of_range(self):
        """Test importance validation"""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(
                title="Test",
                deadline_date=date.today(),
                difficulty=3,
                importance=0,  # Invalid: < 1
                estimated_hours=5.0
            )
        assert "importance" in str(exc_info.value).lower()
    
    def test_negative_estimated_hours(self):
        """Test estimated hours validation"""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(
                title="Test",
                deadline_date=date.today(),
                difficulty=3,
                importance=3,
                estimated_hours=-5.0  # Invalid: negative
            )
        assert "estimated_hours" in str(exc_info.value).lower()
    
    def test_empty_title(self):
        """Test title validation - empty"""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(
                title="   ",  # Invalid: whitespace only
                deadline_date=date.today(),
                difficulty=3,
                importance=3,
                estimated_hours=5.0
            )
        assert "title" in str(exc_info.value).lower()
    
    def test_title_too_long(self):
        """Test title validation - too long"""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(
                title="A" * 501,  # Invalid: > 500 chars
                deadline_date=date.today(),
                difficulty=3,
                importance=3,
                estimated_hours=5.0
            )
        assert "title" in str(exc_info.value).lower()
    
    def test_title_whitespace_cleanup(self):
        """Test title whitespace cleanup"""
        task = TaskCreate(
            title="  Test   Task   ",  # Extra whitespace
            deadline_date=date.today(),
            difficulty=3,
            importance=3,
            estimated_hours=5.0
        )
        assert task.title == "Test Task"  # Cleaned up
    
    def test_deadline_too_far_past(self):
        """Test deadline validation - too far in past"""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(
                title="Test",
                deadline_date=date.today() - timedelta(days=400),  # > 1 year ago
                difficulty=3,
                importance=3,
                estimated_hours=5.0
            )
        assert "deadline" in str(exc_info.value).lower()
    
    def test_invalid_status(self):
        """Test status validation"""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(
                title="Test",
                deadline_date=date.today(),
                difficulty=3,
                importance=3,
                estimated_hours=5.0,
                status="invalid_status"  # Invalid
            )
        assert "status" in str(exc_info.value).lower()
    
    def test_slots_exceed_estimated_hours(self):
        """Test that slot hours cannot exceed estimated hours"""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(
                title="Test",
                deadline_date=date.today(),
                difficulty=3,
                importance=3,
                estimated_hours=5.0,
                slots=[
                    TaskSlotCreate(
                        slot_date=date.today(),
                        start_hour=9.0,
                        hours=3.0
                    ),
                    TaskSlotCreate(
                        slot_date=date.today() + timedelta(days=1),
                        start_hour=9.0,
                        hours=3.0  # Total: 6 hours > 5 estimated
                    )
                ]
            )
        assert "slot" in str(exc_info.value).lower() or "hours" in str(exc_info.value).lower()


class TestTaskSlotValidation:
    """Test TaskSlot schema validation"""
    
    def test_valid_slot(self):
        """Test creating a valid slot"""
        slot = TaskSlotCreate(
            slot_date=date.today(),
            start_hour=9.0,
            hours=2.5
        )
        assert slot.start_hour == 9.0
        assert slot.hours == 2.5
    
    def test_start_hour_negative(self):
        """Test start hour validation - negative"""
        with pytest.raises(ValidationError) as exc_info:
            TaskSlotCreate(
                slot_date=date.today(),
                start_hour=-1.0,  # Invalid
                hours=2.0
            )
        assert "start_hour" in str(exc_info.value).lower()
    
    def test_start_hour_too_large(self):
        """Test start hour validation - >= 24"""
        with pytest.raises(ValidationError) as exc_info:
            TaskSlotCreate(
                slot_date=date.today(),
                start_hour=25.0,  # Invalid
                hours=2.0
            )
        assert "start_hour" in str(exc_info.value).lower()
    
    def test_hours_negative(self):
        """Test hours validation - negative"""
        with pytest.raises(ValidationError) as exc_info:
            TaskSlotCreate(
                slot_date=date.today(),
                start_hour=9.0,
                hours=-1.0  # Invalid
            )
        assert "hours" in str(exc_info.value).lower()
    
    def test_hours_too_large(self):
        """Test hours validation - > 24"""
        with pytest.raises(ValidationError) as exc_info:
            TaskSlotCreate(
                slot_date=date.today(),
                start_hour=9.0,
                hours=25.0  # Invalid
            )
        assert "hours" in str(exc_info.value).lower()
    
    def test_time_range_exceeds_24(self):
        """Test that start_hour + hours cannot exceed 24"""
        with pytest.raises(ValidationError) as exc_info:
            TaskSlotCreate(
                slot_date=date.today(),
                start_hour=23.0,
                hours=2.0  # 23 + 2 = 25 > 24
            )
        assert "24" in str(exc_info.value).lower()


class TestSubjectValidation:
    """Test Subject schema validation"""
    
    def test_valid_subject(self):
        """Test creating a valid subject"""
        subject = SubjectCreate(
            name="Object-Oriented Programming",
            short_name="OOP",
            color="#FF6B6B"
        )
        assert subject.name == "Object-Oriented Programming"
        assert subject.short_name == "OOP"
        assert subject.color == "#FF6B6B"
    
    def test_empty_name(self):
        """Test name validation - empty"""
        with pytest.raises(ValidationError) as exc_info:
            SubjectCreate(
                name="   "  # Invalid: whitespace only
            )
        assert "name" in str(exc_info.value).lower()
    
    def test_name_too_long(self):
        """Test name validation - too long"""
        with pytest.raises(ValidationError) as exc_info:
            SubjectCreate(
                name="A" * 201  # Invalid: > 200 chars
            )
        assert "name" in str(exc_info.value).lower()
    
    def test_short_name_too_long(self):
        """Test short name validation - too long"""
        with pytest.raises(ValidationError) as exc_info:
            SubjectCreate(
                name="Test",
                short_name="A" * 21  # Invalid: > 20 chars
            )
        assert "short_name" in str(exc_info.value).lower()
    
    def test_invalid_color_format(self):
        """Test color validation - invalid format"""
        with pytest.raises(ValidationError) as exc_info:
            SubjectCreate(
                name="Test",
                color="red"  # Invalid: not hex
            )
        assert "color" in str(exc_info.value).lower()
    
    def test_invalid_color_length(self):
        """Test color validation - wrong length"""
        with pytest.raises(ValidationError) as exc_info:
            SubjectCreate(
                name="Test",
                color="#FFF"  # Invalid: too short
            )
        assert "color" in str(exc_info.value).lower()
    
    def test_color_uppercase_conversion(self):
        """Test color is converted to uppercase"""
        subject = SubjectCreate(
            name="Test",
            color="#ff6b6b"  # lowercase
        )
        assert subject.color == "#FF6B6B"  # uppercase
    
    def test_negative_sort_order(self):
        """Test sort order validation - negative"""
        with pytest.raises(ValidationError) as exc_info:
            SubjectCreate(
                name="Test",
                sort_order=-1  # Invalid
            )
        assert "sort_order" in str(exc_info.value).lower()


class TestUserValidation:
    """Test User schema validation"""
    
    def test_valid_user_registration(self):
        """Test valid user registration"""
        user = UserRegister(
            email="test@example.com",
            password="SecurePass123",
            display_name="Test User"
        )
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"
    
    def test_invalid_email(self):
        """Test email validation"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="invalid-email",  # Invalid
                password="SecurePass123",
                display_name="Test"
            )
        assert "email" in str(exc_info.value).lower()
    
    def test_password_too_short(self):
        """Test password validation - too short"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="test@example.com",
                password="Short1",  # < 8 chars
                display_name="Test"
            )
        assert "password" in str(exc_info.value).lower()
    
    def test_password_no_uppercase(self):
        """Test password validation - no uppercase"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="test@example.com",
                password="lowercase123",  # No uppercase
                display_name="Test"
            )
        assert "uppercase" in str(exc_info.value).lower()
    
    def test_password_no_lowercase(self):
        """Test password validation - no lowercase"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="test@example.com",
                password="UPPERCASE123",  # No lowercase
                display_name="Test"
            )
        assert "lowercase" in str(exc_info.value).lower()
    
    def test_password_no_number(self):
        """Test password validation - no number"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="test@example.com",
                password="NoNumbers",  # No digit
                display_name="Test"
            )
        assert "number" in str(exc_info.value).lower()
    
    def test_display_name_invalid_characters(self):
        """Test display name validation - invalid characters"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="test@example.com",
                password="SecurePass123",
                display_name="Test@User!"  # Invalid chars
            )
        assert "display_name" in str(exc_info.value).lower()
    
    def test_user_settings_invalid_chart_type(self):
        """Test user settings validation - invalid chart type"""
        with pytest.raises(ValidationError) as exc_info:
            UserSettingsUpdate(
                chart_type="invalid"  # Invalid
            )
        assert "chart_type" in str(exc_info.value).lower()
    
    def test_user_settings_capacity_out_of_range(self):
        """Test user settings validation - capacity out of range"""
        with pytest.raises(ValidationError) as exc_info:
            UserSettingsUpdate(
                capacity=25  # > 24
            )
        assert "capacity" in str(exc_info.value).lower()
    
    def test_user_settings_invalid_density(self):
        """Test user settings validation - invalid density"""
        with pytest.raises(ValidationError) as exc_info:
            UserSettingsUpdate(
                density="invalid"  # Invalid
            )
        assert "density" in str(exc_info.value).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
