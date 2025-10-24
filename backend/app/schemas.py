"""
Request and response schemas for FastAPI endpoints.

These Pydantic models provide type-safe request body validation and response serialization.
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ============================================================================
# Request Schemas (Input DTOs)
# ============================================================================


class TeacherCreate(BaseModel):
    """Request model for creating a new teacher."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=100, description="Teacher's full name")
    email: EmailStr = Field(..., description="Teacher's email address")
    max_load_hours: float = Field(..., gt=0, description="Maximum teaching hours per week")
    qualified_courses: set[str] = Field(
        default_factory=set, description="Set of course codes this teacher can teach"
    )


class TeacherUpdate(BaseModel):
    """Request model for updating an existing teacher."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, min_length=1, max_length=100, description="Teacher's full name")
    email: EmailStr | None = Field(None, description="Teacher's email address")
    max_load_hours: float | None = Field(None, gt=0, description="Maximum teaching hours per week")
    qualified_courses: set[str] | None = Field(
        None, description="Set of course codes this teacher can teach"
    )


class TimeSlotCreate(BaseModel):
    """Request model for creating a time slot."""

    model_config = ConfigDict(extra="forbid")

    day: int = Field(..., ge=1, le=7, description="Day of week (1=Monday, 7=Sunday)")
    start_hour: float = Field(..., ge=0, le=24, description="Start hour (24-hour format)")
    end_hour: float = Field(..., ge=0, le=24, description="End hour (24-hour format)")


class RoomCreate(BaseModel):
    """Request model for creating a room."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1, description="Room identifier")
    capacity: int = Field(..., gt=0, description="Room seating capacity")
    features: set[str] = Field(default_factory=set, description="Room features (e.g., 'projector')")


class CourseSectionCreate(BaseModel):
    """Request model for creating a course section."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1, description="Section identifier")
    course_code: str = Field(..., min_length=1, description="Course code (e.g., 'CS101')")
    enrollment: int = Field(..., ge=0, description="Number of enrolled students")
    required_feature: str | None = Field(None, description="Required room feature (optional)")


class AssignmentCreate(BaseModel):
    """Request model for creating an assignment."""

    model_config = ConfigDict(extra="forbid")

    section_id: str = Field(..., description="ID of the course section")
    teacher_id: str | None = Field(None, description="ID of the teacher (None if unassigned)")
    room_id: str | None = Field(None, description="ID of the room (None if unassigned)")


class SwapRequest(BaseModel):
    """Request model for swapping a section between teachers."""

    model_config = ConfigDict(extra="forbid")

    section_id: str = Field(..., description="ID of the section to swap")
    from_teacher: str = Field(..., description="Current teacher ID or name")
    to_teacher: str = Field(..., description="Target teacher ID or name")


class RebalanceRequest(BaseModel):
    """Request model for rebalancing teaching assignments."""

    model_config = ConfigDict(extra="forbid")

    max_load_hours: float | None = Field(
        None, description="Optional override for maximum load hours"
    )
    algorithm: str = Field(
        default="greedy",
        pattern="^(greedy|optimal)$",
        description="Rebalancing algorithm: 'greedy' or 'optimal'",
    )


class AssignSectionRequest(BaseModel):
    """Request model for assigning a section to a teacher."""

    model_config = ConfigDict(extra="forbid")

    section_id: str = Field(..., description="ID of the section to assign")
    teacher: str = Field(..., description="ID or name of the teacher")


# ============================================================================
# Response Schemas (Output DTOs)
# ============================================================================


class ScheduleStateResponse(BaseModel):
    """Response model wrapping the full schedule state."""

    model_config = ConfigDict(extra="forbid")

    schedule: dict = Field(..., description="Complete schedule state")


class HealthResponse(BaseModel):
    """Response model for health checks."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., description="Health status")
    agent: str = Field(..., description="Agent type (langgraph or openai)")
