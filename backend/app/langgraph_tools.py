"""LangGraph tool wrappers for university schedule management.

These tools use LangChain's @tool decorator but are specifically designed
for use with LangGraph agents. All tools return properly typed Pydantic models
for type safety and validation. Thread context is managed via LangGraphContext.
"""

from __future__ import annotations

try:
    from langchain_core.tools import tool

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

from .core_tools import (
    core_assign_section,
    core_rebalance,
    core_show_load_distribution,
    core_show_schedule_overview,
    core_show_unassigned,
    core_show_violations,
    core_swap,
)
from .tool_inputs import (
    AssignSectionInput,
    RebalanceInput,
    ShowLoadDistributionInput,
    ShowScheduleOverviewInput,
    ShowUnassignedInput,
    ShowViolationsInput,
    SwapInput,
)
from .langgraph_decorators import lg_tool
from .run_langgraph_wrapper import RunLanggraphContextWrapper
from .tool_responses import (
    AssignmentResponse,
    LoadDistributionResponse,
    RebalancingResponse,
    ScheduleOverviewResponse,
    SwapResponse,
    TeacherLoadInfo,
    UnassignedResponse,
    ViolationsResponse,
)


@tool(args_schema=ShowScheduleOverviewInput)
@lg_tool(
    description="Get an overview of the current schedule state including all teachers, sections, and assignments."
)
def show_schedule_overview(ctx: RunLanggraphContextWrapper | None = None) -> dict:
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


@tool(args_schema=ShowLoadDistributionInput)
@lg_tool(
    description="Compute the teaching load per teacher and return a histogram image path + raw loads."
)
def show_load_distribution(ctx: RunLanggraphContextWrapper | None = None) -> dict:
    """Compute the teaching load per teacher and return a histogram image path + raw loads."""
    result = core_show_load_distribution()
    response = LoadDistributionResponse(**result)
    return response.model_dump(mode="json")


@tool(args_schema=ShowViolationsInput)
@lg_tool(description="Show violations of a given type: overload or conflict.")
def show_violations(ctx: RunLanggraphContextWrapper | None = None, type: str = "") -> dict:
    """Show violations of a given type: overload or conflict."""
    result = core_show_violations(type)
    if "error" in result:
        response = ViolationsResponse(type=type, violations=[])
    else:
        response = ViolationsResponse(**result)
    return response.model_dump(mode="json")


@tool(args_schema=RebalanceInput)
@lg_tool(description="Run optimal rebalancing using OR-Tools to minimize load variance.")
def rebalance(ctx: RunLanggraphContextWrapper | None = None, max_load_hours: float = None) -> dict:
    """Run optimal rebalancing using OR-Tools to minimize load variance."""
    result = core_rebalance(max_load_hours)
    response = RebalancingResponse(**result)
    return response.model_dump(mode="json")


@tool(args_schema=SwapInput)
@lg_tool(description="Swap a section from one teacher to another by names or IDs.")
def swap(
    ctx: RunLanggraphContextWrapper | None = None,
    section_id: str = "",
    from_teacher: str = "",
    to_teacher: str = "",
) -> dict:
    """Swap a section from one teacher to another by names or IDs."""
    result = core_swap(section_id, from_teacher, to_teacher)
    if "error" in result:
        response = SwapResponse(success=False, message=result["error"])
    else:
        response = SwapResponse(
            success=result.get("success", True),
            message=result["message"],
            result=result.get("result"),
        )
    return response.model_dump(mode="json")


@tool(args_schema=ShowUnassignedInput)
@lg_tool(description="Find all unassigned course sections that need teacher assignments.")
def show_unassigned(ctx: RunLanggraphContextWrapper | None = None) -> dict:
    """Find all unassigned course sections that need teacher assignments."""
    result = core_show_unassigned()
    response = UnassignedResponse(**result)
    return response.model_dump(mode="json")


@tool(args_schema=AssignSectionInput)
@lg_tool(description="Assign an unassigned course section to a qualified teacher.")
def assign_section(
    ctx: RunLanggraphContextWrapper | None = None, section_id: str = "", teacher: str = ""
) -> dict:
    """Assign an unassigned course section to a qualified teacher."""
    result = core_assign_section(section_id, teacher)
    if "error" in result:
        response = AssignmentResponse(success=False, message=result["error"])
    else:
        response = AssignmentResponse(
            success=result["success"], message=result["message"], result=result.get("result")
        )
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
