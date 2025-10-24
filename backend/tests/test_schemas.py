"""
Unit tests for FastAPI request/response schemas.

Tests verify that Pydantic models correctly:
1. Accept valid payloads
2. Reject invalid payloads with ValidationError
3. Enforce strict validation (extra fields forbidden)
4. Validate field constraints (min_length, max_length, email, etc.)
"""

import pytest
from pydantic import ValidationError

from app.schemas import (
    AssignmentCreate,
    AssignSectionRequest,
    CourseSectionCreate,
    HealthResponse,
    RebalanceRequest,
    RoomCreate,
    ScheduleStateResponse,
    SwapRequest,
    TeacherCreate,
    TeacherUpdate,
    TimeSlotCreate,
)


class TestTeacherCreate:
    """Tests for TeacherCreate request schema."""

    def test_valid_teacher_create(self):
        """Should accept valid teacher creation payload."""
        payload = {
            "name": "Dr. Alice Smith",
            "email": "alice@example.com",
            "max_load_hours": 12.0,
            "qualified_courses": {"CS101", "CS102"},
        }
        teacher = TeacherCreate(**payload)
        assert teacher.name == "Dr. Alice Smith"
        assert teacher.email == "alice@example.com"
        assert teacher.max_load_hours == 12.0
        assert teacher.qualified_courses == {"CS101", "CS102"}

    def test_missing_required_email_field(self):
        """Should reject payload missing required email field."""
        payload = {
            "name": "Dr. Alice Smith",
            "max_load_hours": 12.0,
            "qualified_courses": {"CS101"},
        }
        with pytest.raises(ValidationError) as exc_info:
            TeacherCreate(**payload)
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("email",) for err in errors)
        assert any(err["type"] == "missing" for err in errors)

    def test_invalid_email_format(self):
        """Should reject invalid email addresses."""
        payload = {
            "name": "Dr. Alice Smith",
            "email": "not-an-email",
            "max_load_hours": 12.0,
        }
        with pytest.raises(ValidationError) as exc_info:
            TeacherCreate(**payload)
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("email",) for err in errors)

    def test_extra_fields_forbidden(self):
        """Should reject payloads with extra unknown fields."""
        payload = {
            "name": "Dr. Alice Smith",
            "email": "alice@example.com",
            "max_load_hours": 12.0,
            "extra_field": "should_not_be_here",
        }
        with pytest.raises(ValidationError) as exc_info:
            TeacherCreate(**payload)
        errors = exc_info.value.errors()
        assert any(err["type"] == "extra_forbidden" for err in errors)

    def test_empty_name_rejected(self):
        """Should reject empty name (min_length=1)."""
        payload = {
            "name": "",
            "email": "alice@example.com",
            "max_load_hours": 12.0,
        }
        with pytest.raises(ValidationError) as exc_info:
            TeacherCreate(**payload)
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("name",) for err in errors)

    def test_name_too_long_rejected(self):
        """Should reject name exceeding max_length=100."""
        payload = {
            "name": "a" * 101,
            "email": "alice@example.com",
            "max_load_hours": 12.0,
        }
        with pytest.raises(ValidationError) as exc_info:
            TeacherCreate(**payload)
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("name",) for err in errors)

    def test_zero_max_load_rejected(self):
        """Should reject max_load_hours <= 0 (constraint: gt=0)."""
        payload = {
            "name": "Dr. Alice Smith",
            "email": "alice@example.com",
            "max_load_hours": 0.0,
        }
        with pytest.raises(ValidationError) as exc_info:
            TeacherCreate(**payload)
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("max_load_hours",) for err in errors)

    def test_qualified_courses_optional_defaults_to_set(self):
        """Should default qualified_courses to empty set if not provided."""
        payload = {
            "name": "Dr. Alice Smith",
            "email": "alice@example.com",
            "max_load_hours": 12.0,
        }
        teacher = TeacherCreate(**payload)
        assert teacher.qualified_courses == set()


class TestTeacherUpdate:
    """Tests for TeacherUpdate request schema."""

    def test_valid_teacher_update_all_fields(self):
        """Should accept valid teacher update with all fields."""
        payload = {
            "name": "Dr. Bob Smith",
            "email": "bob@example.com",
            "max_load_hours": 15.0,
            "qualified_courses": {"CS101", "CS201"},
        }
        update = TeacherUpdate(**payload)
        assert update.name == "Dr. Bob Smith"
        assert update.email == "bob@example.com"

    def test_valid_teacher_update_partial_fields(self):
        """Should accept partial teacher update (all fields optional)."""
        payload = {"name": "Dr. Bob Smith"}
        update = TeacherUpdate(**payload)
        assert update.name == "Dr. Bob Smith"
        assert update.email is None
        assert update.max_load_hours is None

    def test_invalid_email_in_update(self):
        """Should reject invalid email in update."""
        payload = {"email": "invalid-email"}
        with pytest.raises(ValidationError) as exc_info:
            TeacherUpdate(**payload)
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("email",) for err in errors)

    def test_extra_fields_forbidden_in_update(self):
        """Should reject extra fields in teacher update."""
        payload = {
            "name": "Dr. Bob Smith",
            "unknown_field": "value",
        }
        with pytest.raises(ValidationError) as exc_info:
            TeacherUpdate(**payload)
        errors = exc_info.value.errors()
        assert any(err["type"] == "extra_forbidden" for err in errors)


class TestTimeSlotCreate:
    """Tests for TimeSlotCreate request schema."""

    def test_valid_time_slot(self):
        """Should accept valid time slot."""
        payload = {
            "day": 1,
            "start_hour": 9.0,
            "end_hour": 17.0,
        }
        slot = TimeSlotCreate(**payload)
        assert slot.day == 1
        assert slot.start_hour == 9.0
        assert slot.end_hour == 17.0

    def test_day_out_of_range_low(self):
        """Should reject day < 1."""
        payload = {
            "day": 0,
            "start_hour": 9.0,
            "end_hour": 17.0,
        }
        with pytest.raises(ValidationError) as exc_info:
            TimeSlotCreate(**payload)
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("day",) for err in errors)

    def test_day_out_of_range_high(self):
        """Should reject day > 7."""
        payload = {
            "day": 8,
            "start_hour": 9.0,
            "end_hour": 17.0,
        }
        with pytest.raises(ValidationError) as exc_info:
            TimeSlotCreate(**payload)
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("day",) for err in errors)

    def test_start_hour_out_of_range(self):
        """Should reject start_hour outside 0-24 range."""
        payload = {
            "day": 1,
            "start_hour": 25.0,
            "end_hour": 26.0,
        }
        with pytest.raises(ValidationError) as exc_info:
            TimeSlotCreate(**payload)
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("start_hour",) for err in errors)

    def test_end_hour_out_of_range(self):
        """Should reject end_hour outside 0-24 range."""
        payload = {
            "day": 1,
            "start_hour": 9.0,
            "end_hour": -1.0,
        }
        with pytest.raises(ValidationError) as exc_info:
            TimeSlotCreate(**payload)
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("end_hour",) for err in errors)

    def test_extra_fields_forbidden(self):
        """Should reject extra fields in time slot."""
        payload = {
            "day": 1,
            "start_hour": 9.0,
            "end_hour": 17.0,
            "location": "Room 101",
        }
        with pytest.raises(ValidationError) as exc_info:
            TimeSlotCreate(**payload)
        errors = exc_info.value.errors()
        assert any(err["type"] == "extra_forbidden" for err in errors)


class TestRoomCreate:
    """Tests for RoomCreate request schema."""

    def test_valid_room_create(self):
        """Should accept valid room creation."""
        payload = {
            "id": "room_101",
            "capacity": 30,
            "features": {"projector", "whiteboard"},
        }
        room = RoomCreate(**payload)
        assert room.id == "room_101"
        assert room.capacity == 30
        assert room.features == {"projector", "whiteboard"}

    def test_empty_room_id_rejected(self):
        """Should reject empty room ID."""
        payload = {
            "id": "",
            "capacity": 30,
        }
        with pytest.raises(ValidationError) as exc_info:
            RoomCreate(**payload)
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("id",) for err in errors)

    def test_zero_capacity_rejected(self):
        """Should reject capacity <= 0."""
        payload = {
            "id": "room_101",
            "capacity": 0,
        }
        with pytest.raises(ValidationError) as exc_info:
            RoomCreate(**payload)
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("capacity",) for err in errors)

    def test_extra_fields_forbidden(self):
        """Should reject extra fields."""
        payload = {
            "id": "room_101",
            "capacity": 30,
            "building": "Engineering",
        }
        with pytest.raises(ValidationError) as exc_info:
            RoomCreate(**payload)
        errors = exc_info.value.errors()
        assert any(err["type"] == "extra_forbidden" for err in errors)


class TestCourseSectionCreate:
    """Tests for CourseSectionCreate request schema."""

    def test_valid_course_section(self):
        """Should accept valid course section."""
        payload = {
            "id": "CS101-A",
            "course_code": "CS101",
            "enrollment": 25,
            "required_feature": "projector",
        }
        section = CourseSectionCreate(**payload)
        assert section.id == "CS101-A"
        assert section.course_code == "CS101"
        assert section.enrollment == 25
        assert section.required_feature == "projector"

    def test_empty_course_code_rejected(self):
        """Should reject empty course code."""
        payload = {
            "id": "CS101-A",
            "course_code": "",
            "enrollment": 25,
        }
        with pytest.raises(ValidationError) as exc_info:
            CourseSectionCreate(**payload)
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("course_code",) for err in errors)

    def test_negative_enrollment_rejected(self):
        """Should reject negative enrollment."""
        payload = {
            "id": "CS101-A",
            "course_code": "CS101",
            "enrollment": -5,
        }
        with pytest.raises(ValidationError) as exc_info:
            CourseSectionCreate(**payload)
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("enrollment",) for err in errors)

    def test_zero_enrollment_accepted(self):
        """Should accept zero enrollment (ge=0)."""
        payload = {
            "id": "CS101-A",
            "course_code": "CS101",
            "enrollment": 0,
        }
        section = CourseSectionCreate(**payload)
        assert section.enrollment == 0

    def test_extra_fields_forbidden(self):
        """Should reject extra fields."""
        payload = {
            "id": "CS101-A",
            "course_code": "CS101",
            "enrollment": 25,
            "semester": "Fall",
        }
        with pytest.raises(ValidationError) as exc_info:
            CourseSectionCreate(**payload)
        errors = exc_info.value.errors()
        assert any(err["type"] == "extra_forbidden" for err in errors)


class TestAssignmentCreate:
    """Tests for AssignmentCreate request schema."""

    def test_valid_full_assignment(self):
        """Should accept valid assignment with all fields."""
        payload = {
            "section_id": "CS101-A",
            "teacher_id": "t_alice",
            "room_id": "room_101",
        }
        assignment = AssignmentCreate(**payload)
        assert assignment.section_id == "CS101-A"
        assert assignment.teacher_id == "t_alice"
        assert assignment.room_id == "room_101"

    def test_valid_partial_assignment(self):
        """Should accept assignment with only section_id."""
        payload = {"section_id": "CS101-A"}
        assignment = AssignmentCreate(**payload)
        assert assignment.section_id == "CS101-A"
        assert assignment.teacher_id is None
        assert assignment.room_id is None

    def test_empty_section_id_rejected(self):
        """Should reject empty section_id."""
        payload = {
            "section_id": "",
            "teacher_id": "t_alice",
        }
        with pytest.raises(ValidationError) as exc_info:
            AssignmentCreate(**payload)
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("section_id",) for err in errors)

    def test_extra_fields_forbidden(self):
        """Should reject extra fields."""
        payload = {
            "section_id": "CS101-A",
            "teacher_id": "t_alice",
            "notes": "Special scheduling",
        }
        with pytest.raises(ValidationError) as exc_info:
            AssignmentCreate(**payload)
        errors = exc_info.value.errors()
        assert any(err["type"] == "extra_forbidden" for err in errors)


class TestSwapRequest:
    """Tests for SwapRequest request schema."""

    def test_valid_swap_request(self):
        """Should accept valid swap request."""
        payload = {
            "section_id": "CS101-A",
            "from_teacher": "t_alice",
            "to_teacher": "t_bob",
        }
        swap = SwapRequest(**payload)
        assert swap.section_id == "CS101-A"
        assert swap.from_teacher == "t_alice"
        assert swap.to_teacher == "t_bob"

    def test_missing_field_rejected(self):
        """Should reject missing required fields."""
        payload = {
            "section_id": "CS101-A",
            "from_teacher": "t_alice",
        }
        with pytest.raises(ValidationError) as exc_info:
            SwapRequest(**payload)
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("to_teacher",) for err in errors)

    def test_extra_fields_forbidden(self):
        """Should reject extra fields."""
        payload = {
            "section_id": "CS101-A",
            "from_teacher": "t_alice",
            "to_teacher": "t_bob",
            "reason": "Workload balancing",
        }
        with pytest.raises(ValidationError) as exc_info:
            SwapRequest(**payload)
        errors = exc_info.value.errors()
        assert any(err["type"] == "extra_forbidden" for err in errors)


class TestRebalanceRequest:
    """Tests for RebalanceRequest request schema."""

    def test_valid_rebalance_request_with_algorithm(self):
        """Should accept valid rebalance request with algorithm."""
        payload = {
            "max_load_hours": 15.0,
            "algorithm": "greedy",
        }
        req = RebalanceRequest(**payload)
        assert req.max_load_hours == 15.0
        assert req.algorithm == "greedy"

    def test_valid_rebalance_request_optimal_algorithm(self):
        """Should accept optimal algorithm."""
        payload = {"algorithm": "optimal"}
        req = RebalanceRequest(**payload)
        assert req.algorithm == "optimal"

    def test_default_algorithm_is_greedy(self):
        """Should default algorithm to greedy."""
        payload = {}
        req = RebalanceRequest(**payload)
        assert req.algorithm == "greedy"

    def test_invalid_algorithm_rejected(self):
        """Should reject invalid algorithm values."""
        payload = {"algorithm": "invalid_algorithm"}
        with pytest.raises(ValidationError) as exc_info:
            RebalanceRequest(**payload)
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("algorithm",) for err in errors)

    def test_extra_fields_forbidden(self):
        """Should reject extra fields."""
        payload = {
            "algorithm": "greedy",
            "timeout": 60,
        }
        with pytest.raises(ValidationError) as exc_info:
            RebalanceRequest(**payload)
        errors = exc_info.value.errors()
        assert any(err["type"] == "extra_forbidden" for err in errors)


class TestAssignSectionRequest:
    """Tests for AssignSectionRequest request schema."""

    def test_valid_assign_section_request(self):
        """Should accept valid assign section request."""
        payload = {
            "section_id": "CS101-A",
            "teacher": "t_alice",
        }
        req = AssignSectionRequest(**payload)
        assert req.section_id == "CS101-A"
        assert req.teacher == "t_alice"

    def test_missing_section_id_rejected(self):
        """Should reject missing section_id."""
        payload = {"teacher": "t_alice"}
        with pytest.raises(ValidationError) as exc_info:
            AssignSectionRequest(**payload)
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("section_id",) for err in errors)

    def test_extra_fields_forbidden(self):
        """Should reject extra fields."""
        payload = {
            "section_id": "CS101-A",
            "teacher": "t_alice",
            "priority": "high",
        }
        with pytest.raises(ValidationError) as exc_info:
            AssignSectionRequest(**payload)
        errors = exc_info.value.errors()
        assert any(err["type"] == "extra_forbidden" for err in errors)


class TestResponseModels:
    """Tests for response schemas."""

    def test_valid_schedule_state_response(self):
        """Should accept valid schedule state response."""
        payload = {
            "schedule": {
                "teachers": {},
                "rooms": {},
                "sections": {},
            }
        }
        response = ScheduleStateResponse(**payload)
        assert response.schedule is not None

    def test_schedule_state_response_forbids_extra_fields(self):
        """Should reject extra fields in response."""
        payload = {
            "schedule": {},
            "extra": "field",
        }
        with pytest.raises(ValidationError) as exc_info:
            ScheduleStateResponse(**payload)
        errors = exc_info.value.errors()
        assert any(err["type"] == "extra_forbidden" for err in errors)

    def test_valid_health_response(self):
        """Should accept valid health response."""
        payload = {
            "status": "healthy",
            "agent": "langgraph",
        }
        response = HealthResponse(**payload)
        assert response.status == "healthy"
        assert response.agent == "langgraph"

    def test_health_response_forbids_extra_fields(self):
        """Should reject extra fields in health response."""
        payload = {
            "status": "healthy",
            "agent": "langgraph",
            "version": "1.0.0",
        }
        with pytest.raises(ValidationError) as exc_info:
            HealthResponse(**payload)
        errors = exc_info.value.errors()
        assert any(err["type"] == "extra_forbidden" for err in errors)


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_maximum_allowed_name_length(self):
        """Should accept name exactly at max_length=100."""
        payload = {
            "name": "a" * 100,
            "email": "test@example.com",
            "max_load_hours": 10.0,
        }
        teacher = TeacherCreate(**payload)
        assert len(teacher.name) == 100

    def test_maximum_disallowed_name_length(self):
        """Should reject name > max_length=100."""
        payload = {
            "name": "a" * 101,
            "email": "test@example.com",
            "max_load_hours": 10.0,
        }
        with pytest.raises(ValidationError):
            TeacherCreate(**payload)

    def test_float_zero_capacity_rejected(self):
        """Should reject float capacity equal to 0."""
        payload = {
            "id": "room_1",
            "capacity": 0.0,
        }
        with pytest.raises(ValidationError):
            RoomCreate(**payload)

    def test_max_load_hours_boundary_low(self):
        """Should reject max_load_hours at boundary (0.0)."""
        payload = {
            "name": "Dr. Test",
            "email": "test@example.com",
            "max_load_hours": 0.0,
        }
        with pytest.raises(ValidationError):
            TeacherCreate(**payload)

    def test_valid_complex_payload(self):
        """Should handle complex valid payload with all optional fields."""
        payload = {
            "name": "Dr. Complex Teacher",
            "email": "complex@example.com",
            "max_load_hours": 20.5,
            "qualified_courses": {
                "CS101",
                "CS102",
                "CS201",
                "MATH101",
            },
        }
        teacher = TeacherCreate(**payload)
        assert len(teacher.qualified_courses) == 4
