"""Input validation models for LangGraph tools.

These Pydantic models provide argument validation, type safety, and documentation
for LangGraph tool functions. They mirror the input models used in openai_tools.py
for consistency across agent backends.
"""

from pydantic import BaseModel, ConfigDict, Field


class ShowScheduleOverviewInput(BaseModel):
    """Input model for show_schedule_overview tool."""

    model_config = ConfigDict(extra="forbid")

    # This tool takes no arguments


class ShowLoadDistributionInput(BaseModel):
    """Input model for show_load_distribution tool."""

    model_config = ConfigDict(extra="forbid")

    # This tool takes no arguments


class ShowViolationsInput(BaseModel):
    """Input model for show_violations tool."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(
        ...,
        description="Type of violations to check: 'overload' (teacher exceeds max hours) or 'conflict' (teacher has scheduling conflicts)",
        pattern="^(overload|conflict)$",
    )


class RebalanceInput(BaseModel):
    """Input model for rebalance tool."""

    model_config = ConfigDict(extra="forbid")

    max_load_hours: float | None = Field(
        None,
        ge=0,
        description="Optional maximum teaching hours constraint for rebalancing (if None, uses teacher defaults)",
    )


class SwapInput(BaseModel):
    """Input model for swap tool."""

    model_config = ConfigDict(extra="forbid")

    section_id: str = Field(
        ..., min_length=1, description="ID of the section to swap (e.g., 'CS101-A')"
    )
    from_teacher: str = Field(
        ..., min_length=1, description="Name or ID of the teacher who currently has the section"
    )
    to_teacher: str = Field(
        ..., min_length=1, description="Name or ID of the teacher to assign the section to"
    )


class ShowUnassignedInput(BaseModel):
    """Input model for show_unassigned tool."""

    model_config = ConfigDict(extra="forbid")

    # This tool takes no arguments


class AssignSectionInput(BaseModel):
    """Input model for assign_section tool."""

    model_config = ConfigDict(extra="forbid")

    section_id: str = Field(
        ..., min_length=1, description="ID of the unassigned section (e.g., 'CS101-B')"
    )
    teacher: str = Field(
        ..., min_length=1, description="Name or ID of the teacher to assign the section to"
    )
