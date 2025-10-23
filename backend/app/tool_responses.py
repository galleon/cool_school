"""
Pydantic response models for tool outputs.

These models provide type-safe, validated responses for all university scheduling tools,
ensuring consistent structure and enabling proper API documentation.
"""

from typing import Any
from pydantic import BaseModel, Field


class TeacherLoadInfo(BaseModel):
    """Information about a teacher's current workload."""

    name: str = Field(..., description="Teacher's full name")
    current_load: float = Field(..., ge=0.0, description="Current teaching hours per week")
    max_load: float = Field(..., gt=0.0, description="Maximum allowed teaching hours per week")
    utilization: str = Field(..., description="Load utilization percentage (e.g., '75.5%')")


class ScheduleOverviewResponse(BaseModel):
    """Response model for schedule overview tool."""

    message: str = Field(..., description="Status message")
    teachers: dict[str, TeacherLoadInfo] = Field(..., description="Teacher workload information")
    sections: dict[str, Any] = Field(..., description="All course sections")
    assignments: dict[str, Any] = Field(..., description="Section-to-teacher assignments")
    rooms: dict[str, Any] = Field(..., description="All available rooms")


class LoadDistributionResponse(BaseModel):
    """Response model for load distribution analysis."""

    message: str = Field(..., description="Status message")
    histogram_path: str | None = Field(None, description="Path to generated histogram image")
    loads: dict[str, float] = Field(..., description="Teacher name to load mapping")
    statistics: dict[str, float] | None = Field(None, description="Load distribution statistics")


class ViolationInfo(BaseModel):
    """Information about a specific scheduling violation."""

    teacher_name: str = Field(..., description="Name of the teacher involved")
    teacher_id: str = Field(..., description="ID of the teacher involved")
    current_load: float = Field(..., ge=0.0, description="Current teaching load")
    max_load: float | None = Field(
        None, ge=0.0, description="Maximum allowed load (for overload violations)"
    )
    sections: list[str] = Field(default_factory=list, description="Affected course sections")


class ViolationsResponse(BaseModel):
    """Response model for violations analysis."""

    type: str = Field(..., description="Type of violation ('overload' or 'conflict')")
    violations: list[ViolationInfo] = Field(..., description="List of detected violations")
    count: int = Field(..., ge=0, description="Number of violations found")

    def __init__(self, **data):
        super().__init__(**data)
        self.count = len(self.violations)


class RebalancingResult(BaseModel):
    """Information about a rebalancing operation result."""

    teacher_id: str = Field(..., description="Teacher ID")
    teacher_name: str = Field(..., description="Teacher name")
    old_load: float = Field(..., ge=0.0, description="Load before rebalancing")
    new_load: float = Field(..., ge=0.0, description="Load after rebalancing")
    sections_added: list[str] = Field(
        default_factory=list, description="Sections assigned to this teacher"
    )
    sections_removed: list[str] = Field(
        default_factory=list, description="Sections removed from this teacher"
    )


class RebalancingResponse(BaseModel):
    """Response model for rebalancing operations."""

    success: bool = Field(..., description="Whether rebalancing was successful")
    message: str = Field(..., description="Status message")
    changes: list[RebalancingResult] = Field(
        default_factory=list, description="Changes made during rebalancing"
    )
    statistics: dict[str, float] | None = Field(
        None, description="Load distribution statistics after rebalancing"
    )


class SwapResult(BaseModel):
    """Result of a section swap operation."""

    section_id: str = Field(..., description="ID of the swapped section")
    from_teacher: str = Field(..., description="Teacher who gave up the section")
    to_teacher: str = Field(..., description="Teacher who received the section")
    from_teacher_new_load: float = Field(..., ge=0.0, description="From teacher's load after swap")
    to_teacher_new_load: float = Field(..., ge=0.0, description="To teacher's load after swap")


class SwapResponse(BaseModel):
    """Response model for section swap operations."""

    success: bool = Field(..., description="Whether swap was successful")
    message: str = Field(..., description="Status message")
    result: SwapResult | None = Field(None, description="Swap result details if successful")


class UnassignedSection(BaseModel):
    """Information about an unassigned course section."""

    section_id: str = Field(..., description="Section identifier")
    course_code: str = Field(..., description="Course code")
    enrollment: int = Field(..., ge=0, description="Number of enrolled students")
    weekly_hours: float = Field(..., gt=0.0, description="Weekly teaching hours required")
    timeslots: list[str] = Field(..., description="Human-readable time slots")


class UnassignedResponse(BaseModel):
    """Response model for unassigned sections query."""

    message: str = Field(..., description="Status message")
    unassigned_sections: list[UnassignedSection] = Field(
        ..., description="List of unassigned sections"
    )
    count: int = Field(..., ge=0, description="Number of unassigned sections")

    def __init__(self, **data):
        super().__init__(**data)
        self.count = len(self.unassigned_sections)


class AssignmentResult(BaseModel):
    """Result of a section assignment operation."""

    section_id: str = Field(..., description="ID of the assigned section")
    teacher_id: str = Field(..., description="ID of the assigned teacher")
    teacher_name: str = Field(..., description="Name of the assigned teacher")
    teacher_new_load: float = Field(..., ge=0.0, description="Teacher's load after assignment")
    section_hours: float = Field(..., gt=0.0, description="Weekly hours for the assigned section")


class AssignmentResponse(BaseModel):
    """Response model for section assignment operations."""

    success: bool = Field(..., description="Whether assignment was successful")
    message: str = Field(..., description="Status message")
    result: AssignmentResult | None = Field(
        None, description="Assignment result details if successful"
    )


class ToolErrorResponse(BaseModel):
    """Response model for tool errors."""

    success: bool = Field(default=False, description="Always false for error responses")
    error: str = Field(..., description="Error message")
    error_type: str | None = Field(None, description="Type of error")


# Union type for all possible tool responses
ToolResponse = (
    ScheduleOverviewResponse
    | LoadDistributionResponse
    | ViolationsResponse
    | RebalancingResponse
    | SwapResponse
    | UnassignedResponse
    | AssignmentResponse
    | ToolErrorResponse
)


# Response model mapping for tool functions
TOOL_RESPONSE_MODELS = {
    "show_schedule_overview": ScheduleOverviewResponse,
    "show_load_distribution": LoadDistributionResponse,
    "show_violations": ViolationsResponse,
    "rebalance": RebalancingResponse,
    "swap": SwapResponse,
    "show_unassigned": UnassignedResponse,
    "assign_section": AssignmentResponse,
}
