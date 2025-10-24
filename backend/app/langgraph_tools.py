"""LangGraph tool wrappers for university schedule management.

These tools use LangChain's @tool decorator but are specifically designed
for use with LangGraph agents. All tools return properly typed Pydantic models
for type safety and validation.
"""

from __future__ import annotations

try:
    from langchain_core.tools import tool

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

from .core_tools import (
    core_show_schedule_overview,
    core_show_load_distribution,
    core_show_violations,
    core_rebalance,
    core_swap,
    core_show_unassigned,
    core_assign_section,
)
from .tool_responses import (
    ScheduleOverviewResponse,
    TeacherLoadInfo,
    LoadDistributionResponse,
    ViolationsResponse,
    RebalancingResponse,
    SwapResponse,
    UnassignedResponse,
    AssignmentResponse,
    ToolErrorResponse,
)


@tool
def show_schedule_overview() -> dict:
    """Get an overview of the current schedule state including all teachers, sections, and assignments."""
    result = core_show_schedule_overview()
    # Return as dict for JSON serialization
    response = ScheduleOverviewResponse(
        message=result["message"],
        teachers={tid: TeacherLoadInfo(**td) for tid, td in result["teachers"].items()},
        sections=result["sections"],
        assignments=result["assignments"],
        rooms=result["rooms"],
    )
    return response.model_dump(mode="json")


@tool
def show_load_distribution() -> dict:
    """Compute the teaching load per teacher and return a histogram image path + raw loads."""
    result = core_show_load_distribution()
    response = LoadDistributionResponse(**result)
    return response.model_dump(mode="json")


@tool
def show_violations(type: str) -> dict:
    """Show violations of a given type: overload or conflict."""
    result = core_show_violations(type)
    if "error" in result:
        response = ViolationsResponse(type=type, violations=[])
    else:
        response = ViolationsResponse(**result)
    return response.model_dump(mode="json")


@tool
def rebalance(max_load_hours: float = None) -> dict:
    """Run optimal rebalancing using OR-Tools to minimize load variance."""
    result = core_rebalance(max_load_hours)
    response = RebalancingResponse(**result)
    return response.model_dump(mode="json")


@tool
def swap(section_id: str, from_teacher: str, to_teacher: str) -> dict:
    """Swap a section from one teacher to another by names or IDs."""
    result = core_swap(section_id, from_teacher, to_teacher)
    if "error" in result:
        response = SwapResponse(success=False, message=result["error"])
    else:
        response = SwapResponse(success=True, **result)
    return response.model_dump(mode="json")


@tool
def show_unassigned() -> dict:
    """Find all unassigned course sections that need teacher assignments."""
    result = core_show_unassigned()
    response = UnassignedResponse(**result)
    return response.model_dump(mode="json")


@tool
def assign_section(section_id: str, teacher: str) -> dict:
    """Assign an unassigned course section to a qualified teacher."""
    result = core_assign_section(section_id, teacher)
    if "error" in result:
        response = AssignmentResponse(success=False, message=result["error"])
    else:
        response = AssignmentResponse(success=True, **result)
    return response.model_dump(mode="json")


# Export all tools in a list for easy import
UNIVERSITY_TOOLS = [
    show_schedule_overview,
    show_load_distribution,
    show_violations,
    rebalance,
    swap,
    show_unassigned,
    assign_section,
]
