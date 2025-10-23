"""
Core tool functions that are backend-agnostic.
Both OpenAI and LangGraph tools can call these functions.
"""

from typing import Any
from .schedule_state import SCHEDULE_MANAGER


def core_show_schedule_overview() -> dict[str, Any]:
    """Core logic for schedule overview - backend agnostic."""
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


def core_show_load_distribution() -> dict[str, Any]:
    """Core logic for load distribution analysis."""
    import matplotlib.pyplot as plt
    import tempfile
    import os

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


def core_show_violations(violation_type: str) -> dict[str, Any]:
    """Core logic for showing violations."""
    if violation_type == "overload":
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
    elif violation_type == "conflict":
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


def core_rebalance(max_load_hours: float = None) -> dict[str, Any]:
    """Core logic for rebalancing workloads."""
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


def core_swap(section_id: str, from_teacher: str, to_teacher: str) -> dict[str, Any]:
    """Core logic for swapping section assignments."""
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


def core_show_unassigned() -> dict[str, Any]:
    """Core logic for finding unassigned sections."""
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


def core_assign_section(section_id: str, teacher: str) -> dict[str, Any]:
    """Core logic for assigning a section to a teacher."""
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
