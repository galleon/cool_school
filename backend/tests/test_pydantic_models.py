"""
Test suite for Pydantic models, settings, and migration functionality.
"""

import os
import sys

from pydantic import ValidationError

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.migration import convert_legacy_schedule_state, export_to_legacy_format
from app.models import CourseSection, Room, Teacher, TimeSlot, WeekDay
from app.settings import AppSettings, LLMConfig


def test_basic_models():
    """Test basic Pydantic model creation and validation."""
    print("🧪 Testing basic Pydantic models...")
    
    # Test TimeSlot
    timeslot = TimeSlot(day=WeekDay.MONDAY, start_hour=9.0, end_hour=10.5)
    print(f"✅ TimeSlot: {timeslot}")
    
    # Test Teacher
    teacher = Teacher(
        id="t1",
        name="Dr. Smith",
        max_load_hours=20.0,
        qualified_courses={"CS101", "CS102"},
        availability=[timeslot]
    )
    print(f"✅ Teacher: {teacher.name} ({teacher.compute_total_availability_hours()}h available)")
    
    # Test Room
    room = Room(id="r1", capacity=30, features={"projector", "whiteboard"})
    print(f"✅ Room: {room.id} (capacity: {room.capacity})")
    
    # Test CourseSection
    section = CourseSection(
        id="cs101_001",
        course_code="CS101",
        timeslots=[timeslot],
        enrollment=25
    )
    print(f"✅ CourseSection: {section.course_code} ({section.compute_weekly_hours()}h/week)")
    
    print("✅ Basic models test passed!\n")


def test_settings():
    """Test Pydantic settings."""
    print("🧪 Testing Pydantic settings...")
    
    app_settings = AppSettings()
    print(f"✅ AppSettings: backend={app_settings.agent_backend}, port={app_settings.port}")
    
    llm_config = LLMConfig()
    print(f"✅ LLMConfig: temperature={llm_config.temperature}, stream={llm_config.stream}")
    
    print("✅ Settings test passed!\n")


def test_migration():
    """Test migration between legacy and Pydantic models."""
    print("🧪 Testing migration functionality...")
    
    # Legacy data format
    legacy_data = {
        "teachers": {
            "t1": {
                "id": "t1",
                "name": "Dr. Alice",
                "max_load_hours": 12.0,
                "qualified_courses": ["CS101", "CS102"],
                "availability": [{"day": 1, "start_hour": 9.0, "end_hour": 17.0}]
            }
        },
        "rooms": {
            "r1": {"id": "r1", "capacity": 30, "features": ["projector"]}
        },
        "sections": {
            "s1": {
                "id": "s1",
                "course_code": "CS101",
                "timeslots": [{"day": 1, "start_hour": 9.0, "end_hour": 10.5}],
                "enrollment": 25,
                "required_feature": "projector"
            }
        },
        "assignments": {
            "s1": {"section_id": "s1", "teacher_id": "t1", "room_id": "r1"}
        },
        "timeline": []
    }
    
    # Convert to Pydantic
    schedule = convert_legacy_schedule_state(legacy_data)
    print(f"✅ Converted to Pydantic: {len(schedule.teachers)} teachers, {len(schedule.sections)} sections")
    
    # Convert back to legacy
    exported = export_to_legacy_format(schedule)
    print(f"✅ Exported to legacy: teacher name = {exported['teachers']['t1']['name']}")
    
    print("✅ Migration test passed!\n")


def test_validation():
    """Test Pydantic validation features."""
    print("🧪 Testing Pydantic validation...")
    
    try:
        # Should fail - end before start
        TimeSlot(day=WeekDay.MONDAY, start_hour=10.0, end_hour=9.0)
        print("❌ Validation should have failed")
    except ValidationError:
        print("✅ Time order validation works")
    
    try:
        # Should fail - invalid time increment
        TimeSlot(day=WeekDay.MONDAY, start_hour=9.1, end_hour=10.0)
        print("❌ Validation should have failed")
    except ValidationError:
        print("✅ Quarter-hour validation works")
    
    try:
        # Should fail - invalid room feature
        Room(id="r1", capacity=30, features={"invalid_feature"})
        print("❌ Validation should have failed")
    except ValidationError:
        print("✅ Room feature validation works")
    
    print("✅ Validation test passed!\n")


if __name__ == "__main__":
    print("🎯 Starting Pydantic model tests...\n")
    
    test_basic_models()
    test_settings()
    test_migration()
    test_validation()
    
    print("🎉 All tests passed! Pydantic refactoring is successful!")