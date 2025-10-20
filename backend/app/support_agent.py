from __future__ import annotations

import os
import tempfile
from typing import Any

import matplotlib.pyplot as plt
from agents import Agent, RunContextWrapper, function_tool
from chatkit.agents import AgentContext
from pydantic import BaseModel, Field

from .schedule_state import SCHEDULE_MANAGER

SCHEDULING_AGENT_INSTRUCTIONS = """
You are an intelligent scheduling assistant for academic course timetabling and teacher assignment.
You help administrators manage teacher workloads, resolve scheduling conflicts, and optimize
course assignments. Follow these guidelines:

- Always provide clear explanations of the current scheduling state when requested
- When making changes, confirm the outcome and highlight any potential issues
- Use appropriate tools to analyze workload distribution and identify problems
- When conflicts arise, suggest practical solutions using available tools
- Keep responses informative but concise unless detailed analysis is requested

Available tools:
- show_schedule_overview() – Get complete overview of teachers, sections, and assignments
- show_load_distribution() – Analyze teaching load distribution with visualization
- show_violations(type) – Find scheduling violations (overload or conflict)
- show_unassigned() – Find all unassigned course sections that need teachers
- assign_section(section_id, teacher) – Assign an unassigned section to a qualified teacher
- swap(section_id, from_teacher, to_teacher) – Reassign a section to a different teacher
- rebalance(max_load_hours) – Automatically rebalance teaching loads

You have access to data about teachers, course sections, room assignments, and current
teaching assignments. Always use the tools to get current information rather than
making assumptions about the schedule state.
""".strip()


def build_scheduling_agent() -> Agent[AgentContext]:
    """Create the scheduling assistant agent with course management tools."""

    class ViolationInput(BaseModel):
        type: str = Field(
            description="Type of violations: overload or conflict", pattern="^(overload|conflict)$"
        )

    class RebalanceInput(BaseModel):
        max_load_hours: float | None = Field(
            default=None, description="Optional max load hours constraint"
        )

    class SwapInput(BaseModel):
        section_id: str = Field(description="ID of the section to swap")
        from_teacher: str = Field(description="Name or ID of the current teacher")
        to_teacher: str = Field(description="Name or ID of the new teacher")

    @function_tool(
        description_override="Get an overview of the current schedule state including all teachers, sections, and assignments.",
    )
    async def show_schedule_overview(
        ctx: RunContextWrapper[AgentContext],
    ) -> dict[str, Any]:
        """Get an overview of the current schedule state including all teachers, sections, and assignments."""
        state = SCHEDULE_MANAGER.get_state()

        # Add computed loads for teachers
        teacher_loads = {}
        for teacher_id, teacher_data in state["teachers"].items():
            teacher = SCHEDULE_MANAGER.state.teachers[teacher_id]
            load = SCHEDULE_MANAGER.compute_teacher_load(teacher)
            teacher_loads[teacher_id] = {
                "name": teacher_data["name"],
                "current_load": load,
                "max_load": teacher_data["max_load_hours"],
                "utilization": f"{(load / teacher_data['max_load_hours'] * 100):.1f}%"
                if teacher_data["max_load_hours"] > 0
                else "0%",
            }

        return {
            "message": "Schedule overview retrieved",
            "teachers": teacher_loads,
            "sections": state["sections"],
            "assignments": state["assignments"],
            "rooms": state["rooms"],
        }

    @function_tool(
        description_override="Compute the teaching load per teacher and return a histogram image path + raw loads.",
    )
    async def show_load_distribution(
        ctx: RunContextWrapper[AgentContext],
    ) -> dict[str, Any]:
        """Compute the teaching load per teacher and return a histogram image path + raw loads."""
        loads = {
            teacher.name: SCHEDULE_MANAGER.compute_teacher_load(teacher)
            for teacher in SCHEDULE_MANAGER.state.teachers.values()
        }

        try:
            fig = plt.figure(figsize=(10, 6))
            plt.hist(list(loads.values()), bins=5, alpha=0.7, edgecolor="black")
            plt.title("Teaching Load Distribution (hours)")
            plt.xlabel("Hours")
            plt.ylabel("Count")

            tmpdir = tempfile.gettempdir()
            img_path = os.path.join(tmpdir, "load_hist.png")
            fig.savefig(img_path, bbox_inches="tight")
            plt.close(fig)

            return {
                "message": "Load distribution computed.",
                "loads": loads,
                "histogram_path": img_path,
            }
        except Exception as e:
            return {
                "message": "Load distribution computed (chart generation failed).",
                "loads": loads,
                "error": str(e),
            }

    @function_tool(
        description_override="Show violations of a given type: overload or conflict.",
    )
    async def show_violations(
        ctx: RunContextWrapper[AgentContext],
        type: str,
    ) -> dict[str, Any]:
        """Show violations of a given type: overload or conflict."""
        if type == "overload":
            overloads = SCHEDULE_MANAGER.find_overload()
            violations = [
                {
                    "teacher_id": tid,
                    "teacher": SCHEDULE_MANAGER.state.teachers[tid].name,
                    "load": load,
                    "max": max_load,
                }
                for (tid, load, max_load) in overloads
            ]
            return {"type": "overload", "violations": violations}
        elif type == "conflict":
            conflicts = SCHEDULE_MANAGER.find_conflicting_assignments()
            violations = [
                {
                    "teacher_id": tid,
                    "teacher": SCHEDULE_MANAGER.state.teachers[tid].name,
                    "section_id": sid,
                }
                for (tid, sid) in conflicts
            ]
            return {"type": "conflict", "violations": violations}
        else:
            return {"error": "Unknown violation type. Use 'overload' or 'conflict'."}

    @function_tool(
        description_override="Run optimal rebalancing using OR-Tools to minimize load variance.",
    )
    async def rebalance(
        ctx: RunContextWrapper[AgentContext],
        max_load_hours: float | None = None,
    ) -> dict[str, Any]:
        """Run optimal rebalancing using OR-Tools to minimize load variance."""
        # Snapshot the serialized state before running the rebalancer.
        old_snapshot = SCHEDULE_MANAGER.get_state()

        # Run the OR-Tools optimal rebalancer (it mutates the in-memory state).
        SCHEDULE_MANAGER.optimal_rebalance(max_load_hours)

        # Take a new snapshot after rebalancing.
        new_snapshot = SCHEDULE_MANAGER.get_state()

        # Find differences by comparing serialized assignment teacher_ids.
        diffs: list[dict[str, str | None]] = []
        for sid, old_assignment in old_snapshot["assignments"].items():
            old_tid = old_assignment.get("teacher_id")
            new_tid = new_snapshot["assignments"][sid].get("teacher_id")
            if old_tid != new_tid:
                old_name = old_snapshot["teachers"][old_tid]["name"] if old_tid else None
                new_name = new_snapshot["teachers"][new_tid]["name"] if new_tid else None
                diffs.append({"section_id": sid, "from": old_name, "to": new_name})

        # Get loads after rebalancing for summary
        after_loads = {}
        for teacher_id, teacher in SCHEDULE_MANAGER.state.teachers.items():
            after_loads[teacher_id] = {
                "name": teacher.name,
                "load": SCHEDULE_MANAGER.compute_teacher_load(teacher),
            }

        if not diffs:
            return {
                "message": "No rebalancing needed - workload distribution is already optimal (OR-Tools)",
                "teacher_loads": {
                    tid: f"{data['name']}: {data['load']:.1f}h" for tid, data in after_loads.items()
                },
            }

        return {
            "message": f"OR-Tools optimal rebalancing completed - moved {len(diffs)} assignment(s)",
            "changes": diffs,
            "teacher_loads": {
                tid: f"{data['name']}: {data['load']:.1f}h" for tid, data in after_loads.items()
            },
        }

    @function_tool(
        description_override="Swap a section from one teacher to another by names or IDs.",
    )
    async def swap(
        ctx: RunContextWrapper[AgentContext],
        section_id: str,
        from_teacher: str,
        to_teacher: str,
    ) -> dict[str, Any]:
        """Swap a section from one teacher to another by names or IDs."""
        from_teacher_id = SCHEDULE_MANAGER.teacher_name_to_id(from_teacher)
        to_teacher_id = SCHEDULE_MANAGER.teacher_name_to_id(to_teacher)

        if not from_teacher_id:
            return {"error": f"Teacher '{from_teacher}' not found"}

        if not to_teacher_id:
            return {"error": f"Teacher '{to_teacher}' not found"}

        success, reason = SCHEDULE_MANAGER.try_swap(section_id, from_teacher_id, to_teacher_id)

        if not success:
            return {"error": reason}

        return {
            "message": f"Swapped {section_id} from {from_teacher} to {to_teacher}.",
            "success": True,
        }

    class AssignInput(BaseModel):
        section_id: str = Field(description="ID of the section to assign")
        teacher: str = Field(description="Name or ID of the teacher to assign the section to")

    @function_tool(
        description_override="Find all unassigned course sections that need teacher assignments.",
    )
    async def show_unassigned(
        ctx: RunContextWrapper[AgentContext],
    ) -> dict[str, Any]:
        """Find all unassigned course sections that need teacher assignments."""
        state = SCHEDULE_MANAGER.get_state()

        unassigned_sections = []
        for assignment_id, assignment in state["assignments"].items():
            if assignment["teacher_id"] is None:
                section = state["sections"][assignment["section_id"]]
                unassigned_sections.append(
                    {
                        "section_id": assignment["section_id"],
                        "course_code": section["course_code"],
                        "enrollment": section["enrollment"],
                        "required_feature": section["required_feature"],
                        "timeslots": section["timeslots"],
                    }
                )

        return {
            "message": f"Found {len(unassigned_sections)} unassigned section(s)",
            "unassigned_sections": unassigned_sections,
            "total_sections": len(state["sections"]),
            "assigned_sections": len(state["sections"]) - len(unassigned_sections),
        }

    @function_tool(
        description_override="Assign an unassigned course section to a qualified teacher.",
    )
    async def assign_section(
        ctx: RunContextWrapper[AgentContext], /, *, section_id: str, teacher: str
    ) -> dict[str, Any]:
        """Assign an unassigned course section to a qualified teacher."""
        state = SCHEDULE_MANAGER.get_state()

        # Check if section exists and is unassigned
        if section_id not in state["assignments"]:
            return {"error": f"Section {section_id} not found"}

        assignment = state["assignments"][section_id]
        if assignment["teacher_id"] is not None:
            current_teacher = state["teachers"][assignment["teacher_id"]]["name"]
            return {"error": f"Section {section_id} is already assigned to {current_teacher}"}

        # Find teacher by name or ID
        teacher_id = SCHEDULE_MANAGER.teacher_name_to_id(teacher)
        if not teacher_id:
            return {"error": f"Teacher '{teacher}' not found"}

        # Check if teacher is qualified for the course
        section = state["sections"][section_id]
        teacher_obj = SCHEDULE_MANAGER.state.teachers[teacher_id]
        if section["course_code"] not in teacher_obj.qualified_courses:
            qualified_courses = ", ".join(teacher_obj.qualified_courses)
            return {
                "error": f"Teacher {teacher_obj.name} is not qualified to teach {section['course_code']}. Qualified for: {qualified_courses}"
            }

        # Check if assignment would overload the teacher
        current_load = SCHEDULE_MANAGER.compute_teacher_load(teacher_obj)
        section_hours = sum(slot["end_hour"] - slot["start_hour"] for slot in section["timeslots"])

        if current_load + section_hours > teacher_obj.max_load_hours:
            return {
                "error": f"Assignment would overload teacher {teacher_obj.name} ({current_load + section_hours:.1f} > {teacher_obj.max_load_hours} hours)"
            }

        # Make the assignment
        SCHEDULE_MANAGER.state.assignments[section_id].teacher_id = teacher_id
        SCHEDULE_MANAGER.state.log(f"Assigned {section_id} to {teacher_obj.name}", "assignment")

        return {
            "message": f"Successfully assigned {section_id} to {teacher_obj.name}",
            "section_id": section_id,
            "teacher": teacher_obj.name,
            "new_load": f"{current_load + section_hours:.1f}/{teacher_obj.max_load_hours} hours",
        }

    tools = [
        show_schedule_overview,
        show_load_distribution,
        show_violations,
        rebalance,
        swap,
        show_unassigned,
        assign_section,
    ]

    return Agent[AgentContext](
        model="gpt-4o-mini",
        name="Academic Scheduling Assistant",
        instructions=SCHEDULING_AGENT_INSTRUCTIONS,
        tools=tools,  # type: ignore[arg-type]
    )


scheduling_agent = build_scheduling_agent()
