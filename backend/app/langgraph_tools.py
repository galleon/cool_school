"""LangGraph tool wrappers for university schedule management.

These tools use LangChain's @tool decorator but are specifically designed
for use with LangGraph agents.
"""

from __future__ import annotations

from typing import Any, Dict

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


@tool
def show_schedule_overview() -> Dict[str, Any]:
    """Get an overview of the current schedule state including all teachers, sections, and assignments."""
    return core_show_schedule_overview()


@tool
def show_load_distribution() -> Dict[str, Any]:
    """Compute the teaching load per teacher and return a histogram image path + raw loads."""
    return core_show_load_distribution()


@tool
def show_violations(type: str) -> Dict[str, Any]:
    """Show violations of a given type: overload or conflict."""
    return core_show_violations(type)


@tool
def rebalance(max_load_hours: float = None) -> Dict[str, Any]:
    """Run optimal rebalancing using OR-Tools to minimize load variance."""
    return core_rebalance(max_load_hours)


@tool
def swap(section_id: str, from_teacher: str, to_teacher: str) -> Dict[str, Any]:
    """Swap a section from one teacher to another by names or IDs."""
    return core_swap(section_id, from_teacher, to_teacher)


@tool
def show_unassigned() -> Dict[str, Any]:
    """Find all unassigned course sections that need teacher assignments."""
    return core_show_unassigned()


@tool
def assign_section(section_id: str, teacher: str) -> Dict[str, Any]:
    """Assign an unassigned course section to a qualified teacher."""
    return core_assign_section(section_id, teacher)


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
