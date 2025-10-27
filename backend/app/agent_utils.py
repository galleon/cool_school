"""Shared utilities for agent server implementations."""

from __future__ import annotations

from .schedule_state import SCHEDULE_MANAGER


def format_schedule_context() -> str:
    """Format the current schedule state as context for the agent."""
    state = SCHEDULE_MANAGER.get_state()

    # Summary of teachers and their loads
    teacher_summaries = []
    for teacher_id, teacher_data in state["teachers"].items():
        teacher = SCHEDULE_MANAGER.state.teachers[teacher_id]
        load = SCHEDULE_MANAGER.compute_teacher_load(teacher)
        utilization = (
            (load / teacher_data["max_load_hours"] * 100)
            if teacher_data["max_load_hours"] > 0
            else 0
        )
        qualified_courses = ", ".join(teacher_data["qualified_courses"])
        teacher_summaries.append(
            f"- {teacher_data['name']} (qualified: {qualified_courses}): "
            f"{load:.1f}/{teacher_data['max_load_hours']:.1f} hours ({utilization:.1f}%)"
        )

    # Count of sections and assignments
    total_sections = len(state["sections"])
    assigned_sections = len([a for a in state["assignments"].values() if a["teacher_id"]])
    unassigned_sections = total_sections - assigned_sections

    # Recent timeline entries
    timeline = state["timeline"][:3]
    recent = "\n".join(f"  * {entry['entry']} ({entry['timestamp']})" for entry in timeline)

    return (
        "Current Schedule State\n"
        f"Total Sections: {total_sections} (Assigned: {assigned_sections}, Unassigned: {unassigned_sections})\n"
        "Teacher Workloads:\n"
        f"{chr(10).join(teacher_summaries)}\n"
        "Recent Changes:\n"
        f"{recent or '  * No recent changes recorded.'}"
    )
