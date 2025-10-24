"""
Pydantic models for the Academic Scheduling Assistant.

This module defines type-safe, validated data models for all core entities
in the scheduling system using Pydantic BaseModel classes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class WeekDay(int, Enum):
    """Enumeration for days of the week."""

    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


class TimeSlot(BaseModel):
    """Represents a time slot for scheduling with validation."""

    model_config = ConfigDict(extra="forbid")

    day: WeekDay = Field(..., description="Day of the week (1=Monday, 7=Sunday)")
    start_hour: float = Field(
        ..., ge=0.0, le=24.0, description="Start time in 24-hour format (e.g., 9.0 = 9:00 AM)"
    )
    end_hour: float = Field(
        ..., ge=0.0, le=24.0, description="End time in 24-hour format (e.g., 17.0 = 5:00 PM)"
    )

    @model_validator(mode="after")
    def validate_time_order(self) -> "TimeSlot":
        """Ensure end_hour is after start_hour."""
        if self.end_hour <= self.start_hour:
            raise ValueError("end_hour must be greater than start_hour")
        return self

    @field_validator("start_hour", "end_hour")
    @classmethod
    def validate_quarter_hours(cls, v: float) -> float:
        """Ensure times are in quarter-hour increments."""
        if (v * 4) % 1 != 0:
            raise ValueError(
                "Hours must be in quarter-hour increments (e.g., 9.0, 9.25, 9.5, 9.75)"
            )
        return v

    def __str__(self) -> str:
        """Human-readable string representation."""
        if isinstance(self.day, WeekDay):
            day_name = self.day.name.capitalize()
        else:
            # Handle case where day is stored as int
            day_names = {
                1: "Monday",
                2: "Tuesday",
                3: "Wednesday",
                4: "Thursday",
                5: "Friday",
                6: "Saturday",
                7: "Sunday",
            }
            day_name = day_names.get(self.day, f"Day{self.day}")
        start_time = f"{int(self.start_hour):02d}:{int((self.start_hour % 1) * 60):02d}"
        end_time = f"{int(self.end_hour):02d}:{int((self.end_hour % 1) * 60):02d}"
        return f"{day_name} {start_time}-{end_time}"


class Teacher(BaseModel):
    """Represents a teacher with qualifications and availability."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1, max_length=50, description="Unique teacher identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Teacher's full name")
    email: EmailStr = Field(..., description="Teacher's email address")
    max_load_hours: float = Field(
        ..., gt=0.0, le=40.0, description="Maximum teaching hours per week"
    )
    qualified_courses: set[str] = Field(
        default_factory=set, description="Set of course codes the teacher is qualified to teach"
    )
    availability: list[TimeSlot] = Field(
        default_factory=list, description="Available time slots for teaching"
    )

    @field_validator("qualified_courses")
    @classmethod
    def validate_course_codes(cls, v: set[str]) -> set[str]:
        """Ensure all course codes follow a valid format."""
        for course_code in v:
            if not course_code or len(course_code) > 20:
                raise ValueError(f'Course code "{course_code}" must be 1-20 characters')
            if not course_code.replace("-", "").replace("_", "").isalnum():
                raise ValueError(
                    f'Course code "{course_code}" must be alphanumeric with optional hyphens/underscores'
                )
        return v

    @field_validator("availability")
    @classmethod
    def validate_no_overlapping_slots(cls, v: list[TimeSlot]) -> list[TimeSlot]:
        """Ensure teacher availability slots don't overlap."""
        for i, slot1 in enumerate(v):
            for j, slot2 in enumerate(v[i + 1 :], i + 1):
                if slot1.day == slot2.day and not (
                    slot1.end_hour <= slot2.start_hour or slot2.end_hour <= slot1.start_hour
                ):
                    raise ValueError(f"Overlapping availability slots: {slot1} and {slot2}")
        return v

    def compute_total_availability_hours(self) -> float:
        """Calculate total available teaching hours per week."""
        return sum((slot.end_hour - slot.start_hour) for slot in self.availability)


class Room(BaseModel):
    """Represents a classroom or teaching space."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1, max_length=50, description="Unique room identifier")
    capacity: int = Field(..., gt=0, le=1000, description="Maximum number of students")
    features: set[str] = Field(
        default_factory=set, description="Available room features (e.g., projector, computers)"
    )

    @field_validator("features")
    @classmethod
    def validate_features(cls, v: set[str]) -> set[str]:
        """Ensure feature names are valid."""
        valid_features = {
            "projector",
            "computers",
            "whiteboard",
            "smartboard",
            "audio",
            "video",
            "lab_equipment",
            "wheelchair_accessible",
        }
        for feature in v:
            if feature not in valid_features:
                raise ValueError(
                    f"Unknown room feature: {feature}. Valid features: {', '.join(valid_features)}"
                )
        return v


class CourseSection(BaseModel):
    """Represents a specific section of a course."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1, max_length=50, description="Unique section identifier")
    course_code: str = Field(
        ..., min_length=1, max_length=20, description="Course code (e.g., CS101)"
    )
    timeslots: list[TimeSlot] = Field(
        ..., min_items=1, description="Scheduled time slots for this section"
    )
    enrollment: int = Field(..., ge=0, le=1000, description="Number of enrolled students")
    required_feature: str | None = Field(None, description="Required room feature for this section")

    @field_validator("course_code")
    @classmethod
    def validate_course_code_format(cls, v: str) -> str:
        """Validate course code format."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Course code must be alphanumeric with optional hyphens/underscores")
        return v.upper()  # Normalize to uppercase

    @field_validator("timeslots")
    @classmethod
    def validate_no_overlapping_timeslots(cls, v: list[TimeSlot]) -> list[TimeSlot]:
        """Ensure section timeslots don't overlap."""
        for i, slot1 in enumerate(v):
            for j, slot2 in enumerate(v[i + 1 :], i + 1):
                if slot1.day == slot2.day and not (
                    slot1.end_hour <= slot2.start_hour or slot2.end_hour <= slot1.start_hour
                ):
                    raise ValueError(f"Overlapping timeslots in section: {slot1} and {slot2}")
        return v

    def compute_weekly_hours(self) -> float:
        """Calculate total weekly hours for this section."""
        return sum((slot.end_hour - slot.start_hour) for slot in self.timeslots)


class Assignment(BaseModel):
    """Represents an assignment of a teacher to a section in a room."""

    model_config = ConfigDict(extra="forbid")

    section_id: str = Field(..., min_length=1, description="ID of the assigned section")
    teacher_id: str | None = Field(
        None, description="ID of the assigned teacher (None if unassigned)"
    )
    room_id: str | None = Field(None, description="ID of the assigned room (None if unassigned)")
    assigned_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the assignment was made",
    )

    @field_validator("assigned_at")
    @classmethod
    def validate_assignment_time(cls, v: datetime) -> datetime:
        """Ensure assignment time is not in the future."""
        now = datetime.now(timezone.utc)
        if v > now:
            raise ValueError("Assignment time cannot be in the future")
        return v

    @model_validator(mode="after")
    def validate_assignment_consistency(self) -> "Assignment":
        """Ensure assignment is consistent."""
        # Allow partial assignments for flexibility
        if self.room_id and not self.teacher_id:
            raise ValueError("Cannot assign room without teacher")
        return self


class TimelineEntryKind(str, Enum):
    """Types of timeline entries."""

    SYSTEM = "system"
    ASSIGNMENT = "assignment"
    REBALANCING = "rebalancing"
    CONFLICT = "conflict"
    ERROR = "error"


class TimelineEntry(BaseModel):
    """Represents an entry in the scheduling timeline/audit log."""

    model_config = ConfigDict(extra="forbid")

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="When the event occurred"
    )
    kind: TimelineEntryKind = Field(..., description="Type of timeline entry")
    entry: str = Field(
        ..., min_length=1, max_length=500, description="Human-readable description of the event"
    )

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is not in the future."""
        now = datetime.now(timezone.utc)
        if v > now:
            raise ValueError("Timeline timestamp cannot be in the future")
        return v


class ScheduleState(BaseModel):
    """Complete state of the scheduling system."""

    model_config = ConfigDict(extra="forbid")

    teachers: dict[str, Teacher] = Field(
        default_factory=dict, description="All teachers indexed by ID"
    )
    rooms: dict[str, Room] = Field(default_factory=dict, description="All rooms indexed by ID")
    sections: dict[str, CourseSection] = Field(
        default_factory=dict, description="All course sections indexed by ID"
    )
    assignments: dict[str, Assignment] = Field(
        default_factory=dict, description="All assignments indexed by section ID"
    )
    timeline: list[TimelineEntry] = Field(
        default_factory=list, description="Chronological log of scheduling events"
    )

    @model_validator(mode="after")
    def validate_assignment_references(self) -> "ScheduleState":
        """Ensure all assignments reference valid sections, teachers, and rooms."""
        for section_id, assignment in self.assignments.items():
            # Validate section exists
            if section_id not in self.sections:
                raise ValueError(f"Assignment references non-existent section: {section_id}")

            # Validate teacher exists (if assigned)
            if assignment.teacher_id and assignment.teacher_id not in self.teachers:
                raise ValueError(
                    f"Assignment references non-existent teacher: {assignment.teacher_id}"
                )

            # Validate room exists (if assigned)
            if assignment.room_id and assignment.room_id not in self.rooms:
                raise ValueError(f"Assignment references non-existent room: {assignment.room_id}")

        return self

    @field_validator("timeline")
    @classmethod
    def validate_timeline_chronology(cls, v: list[TimelineEntry]) -> list[TimelineEntry]:
        """Ensure timeline entries are in chronological order."""
        for i in range(1, len(v)):
            if v[i].timestamp < v[i - 1].timestamp:
                raise ValueError(f"Timeline entries out of order at index {i}")
        return v

    def get_teacher_load(self, teacher_id: str) -> float:
        """Calculate current teaching load for a teacher."""
        if teacher_id not in self.teachers:
            raise ValueError(f"Teacher not found: {teacher_id}")

        total_hours = 0.0
        for assignment in self.assignments.values():
            if assignment.teacher_id == teacher_id:
                section = self.sections[assignment.section_id]
                total_hours += section.compute_weekly_hours()

        return total_hours

    def get_unassigned_sections(self) -> list[str]:
        """Get list of section IDs that don't have teacher assignments."""
        return [
            section_id
            for section_id, assignment in self.assignments.items()
            if not assignment.teacher_id
        ]

    def add_timeline_entry(self, kind: TimelineEntryKind, message: str) -> None:
        """Add a new entry to the timeline."""
        entry = TimelineEntry(kind=kind, entry=message)
        self.timeline.append(entry)


# Example usage and validation
if __name__ == "__main__":
    # Example: Create a validated teacher
    teacher = Teacher(
        id="t_alice",
        name="Dr. Alice Smith",
        email="alice@example.com",
        max_load_hours=12.0,
        qualified_courses={"CS101", "CS102"},
        availability=[
            TimeSlot(day=WeekDay.MONDAY, start_hour=9.0, end_hour=17.0),
            TimeSlot(day=WeekDay.TUESDAY, start_hour=9.0, end_hour=15.0),
        ],
    )

    print(f"Created teacher: {teacher.name}")
    print(f"Total availability: {teacher.compute_total_availability_hours()} hours")

    # Example: Create a validated room
    room = Room(id="room_101", capacity=30, features={"projector", "whiteboard"})

    print(f"Created room: {room.id} with capacity {room.capacity}")
