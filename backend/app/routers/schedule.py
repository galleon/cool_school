"""
FastAPI router for scheduling operations with proper Pydantic response models.

This router provides endpoints for:
- Getting schedule state and health status
- Managing teachers, rooms, and sections
- Performing scheduling operations (assign, swap, rebalance)
"""

from typing import Any

from fastapi import APIRouter, Query

from .schemas import (
    AssignSectionRequest,
    HealthResponse,
    RebalanceRequest,
    ScheduleStateResponse,
    SwapRequest,
)
from .schedule_state import SCHEDULE_MANAGER
from .tool_responses import (
    AssignmentResponse,
    RebalancingResponse,
    ScheduleOverviewResponse,
    SwapResponse,
    UnassignedResponse,
)

# Create router
router = APIRouter(prefix="/schedule", tags=["scheduling"])


# ============================================================================
# State Management Endpoints
# ============================================================================


@router.get(
    "/state",
    response_model=ScheduleStateResponse,
    summary="Get Schedule State",
    description="Retrieve the current schedule state including all teachers, rooms, sections, and assignments.",
)
async def get_schedule_state(
    thread_id: str | None = Query(None, description="Optional ChatKit thread identifier"),
) -> ScheduleStateResponse:
    """
    Get the current schedule state.

    Returns:
        ScheduleStateResponse: Complete schedule state with all entities.
    """
    data = SCHEDULE_MANAGER.get_state()
    return ScheduleStateResponse(schedule=data)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Verify the scheduling service is operational.",
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        HealthResponse: Service status and agent type.
    """
    return HealthResponse(status="healthy", agent="scheduling-api")


# ============================================================================
# View Endpoints (GET)
# ============================================================================


@router.get(
    "/overview",
    response_model=ScheduleOverviewResponse,
    summary="Schedule Overview",
    description="Get an overview of the schedule including teacher workloads and assignments.",
)
async def get_schedule_overview() -> ScheduleOverviewResponse:
    """
    Get schedule overview with teacher workload information.

    Returns:
        ScheduleOverviewResponse: Schedule overview with teacher load info.
    """
    from .core_tools import core_show_schedule_overview

    result = core_show_schedule_overview()
    return ScheduleOverviewResponse(**result)


@router.get(
    "/unassigned",
    response_model=UnassignedResponse,
    summary="Get Unassigned Sections",
    description="List all course sections that have not yet been assigned to a teacher.",
)
async def get_unassigned_sections() -> UnassignedResponse:
    """
    Get unassigned course sections.

    Returns:
        UnassignedResponse: List of sections awaiting assignment.
    """
    from .core_tools import core_show_unassigned

    result = core_show_unassigned()
    return UnassignedResponse(**result)


# ============================================================================
# Action Endpoints (POST/PUT)
# ============================================================================


@router.post(
    "/assign",
    response_model=AssignmentResponse,
    summary="Assign Section to Teacher",
    description="Assign an unassigned course section to a qualified teacher.",
)
async def assign_section(request: AssignSectionRequest) -> AssignmentResponse:
    """
    Assign a section to a teacher.

    Args:
        request: AssignSectionRequest containing section_id and teacher identifier.

    Returns:
        AssignmentResponse: Result of the assignment operation.
    """
    from .core_tools import core_assign_section

    result = core_assign_section(request.section_id, request.teacher)
    if "error" in result:
        return AssignmentResponse(success=False, message=result["error"])
    return AssignmentResponse(success=True, message="Assignment successful", **result)


@router.post(
    "/swap",
    response_model=SwapResponse,
    summary="Swap Section Between Teachers",
    description="Move a course section from one teacher to another.",
)
async def swap_section(request: SwapRequest) -> SwapResponse:
    """
    Swap a section between two teachers.

    Args:
        request: SwapRequest with section_id and teacher identifiers.

    Returns:
        SwapResponse: Result of the swap operation.
    """
    from .core_tools import core_swap

    result = core_swap(request.section_id, request.from_teacher, request.to_teacher)
    if "error" in result:
        return SwapResponse(success=False, message=result["error"])
    return SwapResponse(success=True, message="Swap successful", **result)


@router.post(
    "/rebalance",
    response_model=RebalancingResponse,
    summary="Rebalance Teaching Assignments",
    description="Automatically redistribute teaching assignments to balance workloads.",
)
async def rebalance_assignments(request: RebalanceRequest) -> RebalancingResponse:
    """
    Rebalance teaching assignments using specified algorithm.

    Args:
        request: RebalanceRequest with optional max_load_hours and algorithm choice.

    Returns:
        RebalancingResponse: Changes made during rebalancing with updated statistics.
    """
    from .core_tools import core_rebalance

    result = core_rebalance(request.max_load_hours)
    return RebalancingResponse(**result)
