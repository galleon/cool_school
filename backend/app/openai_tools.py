"""OpenAI ChatKit tool wrappers for university schedule management.

These tools use ChatKit's @function_tool decorator and are specifically designed
for use with OpenAI-based agents. All tools return properly typed Pydantic models
for type safety and validation.
"""

from __future__ import annotations

from agents import RunContextWrapper, function_tool
from chatkit.agents import AgentContext

from .core_tools import (
    core_assign_section,
    core_rebalance,
    core_reset_schedule,
    core_show_load_distribution,
    core_show_schedule_overview,
    core_show_unassigned,
    core_show_violations,
    core_swap,
)
from .tool_responses import (
    AssignmentResponse,
    AssignmentResult,
    LoadDistributionResponse,
    RebalancingResponse,
    ResetScheduleResponse,
    ScheduleOverviewResponse,
    SwapResponse,
    UnassignedResponse,
    ViolationsResponse,
)


# OpenAI ChatKit tool functions
@function_tool(
    description_override="Get an overview of the current schedule state including all teachers, sections, and assignments.",
)
async def show_schedule_overview(
    ctx: RunContextWrapper[AgentContext],
) -> ScheduleOverviewResponse:
    """Get an overview of the current schedule state including all teachers, sections, and assignments."""
    result = core_show_schedule_overview()
    return ScheduleOverviewResponse(**result)


@function_tool(
    description_override="Compute the teaching load per teacher and return a histogram image path + raw loads.",
)
async def show_load_distribution(
    ctx: RunContextWrapper[AgentContext],
) -> LoadDistributionResponse:
    """Compute the teaching load per teacher and return a histogram image path + raw loads."""
    result = core_show_load_distribution()
    return LoadDistributionResponse(**result)


@function_tool(
    description_override="Show violations of a given type: overload or conflict.",
)
async def show_violations(
    ctx: RunContextWrapper[AgentContext],
    type: str,
) -> ViolationsResponse:
    """Show violations of a given type: overload or conflict."""
    result = core_show_violations(type)
    if "error" in result:
        # Handle error case - return empty violations for this type
        return ViolationsResponse(type=type, violations=[])
    return ViolationsResponse(**result)


@function_tool(
    description_override="Run optimal rebalancing using OR-Tools to minimize load variance.",
)
async def rebalance(
    ctx: RunContextWrapper[AgentContext],
    max_load_hours: float | None = None,
) -> RebalancingResponse:
    """Run optimal rebalancing using OR-Tools to minimize load variance."""
    result = core_rebalance(max_load_hours)
    return RebalancingResponse(**result)


@function_tool(
    description_override="Swap a section from one teacher to another by names or IDs.",
)
async def swap(
    ctx: RunContextWrapper[AgentContext],
    section_id: str,
    from_teacher: str,
    to_teacher: str,
) -> SwapResponse:
    """Swap a section from one teacher to another by names or IDs."""
    result = core_swap(section_id, from_teacher, to_teacher)
    if "error" in result:
        return SwapResponse(success=False, message=result["error"])
    return SwapResponse(success=True, **result)


@function_tool(
    description_override="Find all unassigned course sections that need teacher assignments.",
)
async def show_unassigned(
    ctx: RunContextWrapper[AgentContext],
) -> UnassignedResponse:
    """Find all unassigned course sections that need teacher assignments."""
    result = core_show_unassigned()
    return UnassignedResponse(**result)


@function_tool(
    description_override="Assign an unassigned course section to a qualified teacher.",
)
async def assign_section(
    ctx: RunContextWrapper[AgentContext], /, *, section_id: str, teacher: str
) -> AssignmentResponse:
    """Assign an unassigned course section to a qualified teacher."""
    result = core_assign_section(section_id, teacher)
    if "error" in result:
        return AssignmentResponse(success=False, message=result["error"], result=None)
    # Extract the nested result dict and flatten it into AssignmentResult
    return AssignmentResponse(
        success=True, message=result["message"], result=AssignmentResult(**result["result"])
    )


@function_tool(
    description_override="Reset the entire schedule to its initial state with sample data.",
)
async def reset_schedule(
    ctx: RunContextWrapper[AgentContext],
) -> ResetScheduleResponse:
    """Reset the entire schedule to its initial state with sample data."""
    result = core_reset_schedule()
    return ResetScheduleResponse(**result)


# Export all tools in a list for easy import
OPENAI_TOOLS = [
    show_schedule_overview,
    show_load_distribution,
    show_violations,
    rebalance,
    swap,
    show_unassigned,
    assign_section,
    reset_schedule,
]
