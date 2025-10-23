"""
Migration utility to convert between legacy @dataclass models and new Pydantic models.

This module provides utilities to help migrate from the old dataclass-based 
schedule_state.py models to the new Pydantic-based models.py classes.
"""

from typing import Dict, List, Any

from .models import (
    TimeSlot, Teacher, Room, CourseSection, Assignment, 
    ScheduleState, TimelineEntry, TimelineEntryKind, WeekDay
)


def convert_legacy_timeslot(legacy_data: Dict[str, Any]) -> TimeSlot:
    """Convert legacy timeslot dictionary to Pydantic TimeSlot."""
    return TimeSlot(
        day=WeekDay(legacy_data["day"]),
        start_hour=legacy_data["start_hour"],
        end_hour=legacy_data["end_hour"]
    )


def convert_legacy_teacher(legacy_data: Dict[str, Any]) -> Teacher:
    """Convert legacy teacher dictionary to Pydantic Teacher."""
    availability = []
    for slot_data in legacy_data.get("availability", []):
        availability.append(convert_legacy_timeslot(slot_data))
    
    return Teacher(
        id=legacy_data["id"],
        name=legacy_data["name"],
        max_load_hours=legacy_data["max_load_hours"],
        qualified_courses=set(legacy_data.get("qualified_courses", [])),
        availability=availability
    )


def convert_legacy_room(legacy_data: Dict[str, Any]) -> Room:
    """Convert legacy room dictionary to Pydantic Room."""
    return Room(
        id=legacy_data["id"],
        capacity=legacy_data["capacity"],
        features=set(legacy_data.get("features", []))
    )


def convert_legacy_section(legacy_data: Dict[str, Any]) -> CourseSection:
    """Convert legacy section dictionary to Pydantic CourseSection."""
    timeslots = []
    for slot_data in legacy_data.get("timeslots", []):
        timeslots.append(convert_legacy_timeslot(slot_data))
    
    return CourseSection(
        id=legacy_data["id"],
        course_code=legacy_data["course_code"],
        timeslots=timeslots,
        enrollment=legacy_data["enrollment"],
        required_feature=legacy_data.get("required_feature")
    )


def convert_legacy_assignment(legacy_data: Dict[str, Any]) -> Assignment:
    """Convert legacy assignment dictionary to Pydantic Assignment."""
    return Assignment(
        section_id=legacy_data["section_id"],
        teacher_id=legacy_data.get("teacher_id"),
        room_id=legacy_data.get("room_id")
        # assigned_at will be set to current time by default
    )


def convert_legacy_schedule_state(legacy_data: Dict[str, Any]) -> ScheduleState:
    """Convert legacy schedule state dictionary to Pydantic ScheduleState."""
    # Convert teachers
    teachers = {}
    for teacher_id, teacher_data in legacy_data.get("teachers", {}).items():
        teachers[teacher_id] = convert_legacy_teacher(teacher_data)
    
    # Convert rooms
    rooms = {}
    for room_id, room_data in legacy_data.get("rooms", {}).items():
        rooms[room_id] = convert_legacy_room(room_data)
    
    # Convert sections
    sections = {}
    for section_id, section_data in legacy_data.get("sections", {}).items():
        sections[section_id] = convert_legacy_section(section_data)
    
    # Convert assignments
    assignments = {}
    for section_id, assignment_data in legacy_data.get("assignments", {}).items():
        assignments[section_id] = convert_legacy_assignment(assignment_data)
    
    # Convert timeline (if present)
    timeline = []
    for entry_data in legacy_data.get("timeline", []):
        timeline.append(TimelineEntry(
            kind=TimelineEntryKind(entry_data.get("kind", "system")),
            entry=entry_data["entry"]
            # timestamp will be set to current time by default
        ))
    
    return ScheduleState(
        teachers=teachers,
        rooms=rooms,
        sections=sections,
        assignments=assignments,
        timeline=timeline
    )


def export_to_legacy_format(schedule_state: ScheduleState) -> Dict[str, Any]:
    """Export Pydantic ScheduleState to legacy dictionary format for backward compatibility."""
    return {
        "teachers": {
            teacher_id: {
                "id": teacher.id,
                "name": teacher.name,
                "max_load_hours": teacher.max_load_hours,
                "qualified_courses": list(teacher.qualified_courses),
                "availability": [
                    {
                        "day": slot.day,
                        "start_hour": slot.start_hour,
                        "end_hour": slot.end_hour
                    }
                    for slot in teacher.availability
                ]
            }
            for teacher_id, teacher in schedule_state.teachers.items()
        },
        "rooms": {
            room_id: {
                "id": room.id,
                "capacity": room.capacity,
                "features": list(room.features)
            }
            for room_id, room in schedule_state.rooms.items()
        },
        "sections": {
            section_id: {
                "id": section.id,
                "course_code": section.course_code,
                "timeslots": [
                    {
                        "day": slot.day,
                        "start_hour": slot.start_hour,
                        "end_hour": slot.end_hour
                    }
                    for slot in section.timeslots
                ],
                "enrollment": section.enrollment,
                "required_feature": section.required_feature
            }
            for section_id, section in schedule_state.sections.items()
        },
        "assignments": {
            section_id: {
                "section_id": assignment.section_id,
                "teacher_id": assignment.teacher_id,
                "room_id": assignment.room_id
            }
            for section_id, assignment in schedule_state.assignments.items()
        },
        "timeline": [
            {
                "kind": entry.kind,
                "entry": entry.entry,
                "timestamp": entry.timestamp.isoformat()
            }
            for entry in schedule_state.timeline
        ]
    }


# Example usage for testing migration
if __name__ == "__main__":
    # Example legacy data
    legacy_data = {
        "teachers": {
            "t1": {
                "id": "t1",
                "name": "Dr. Alice",
                "max_load_hours": 12.0,
                "qualified_courses": ["CS101", "CS102"],
                "availability": [
                    {"day": 1, "start_hour": 9.0, "end_hour": 17.0}
                ]
            }
        },
        "rooms": {
            "r1": {
                "id": "r1",
                "capacity": 30,
                "features": ["projector"]
            }
        },
        "sections": {
            "s1": {
                "id": "s1",
                "course_code": "CS101",
                "timeslots": [
                    {"day": 1, "start_hour": 9.0, "end_hour": 10.5}
                ],
                "enrollment": 25,
                "required_feature": "projector"
            }
        },
        "assignments": {
            "s1": {
                "section_id": "s1",
                "teacher_id": "t1",
                "room_id": "r1"
            }
        },
        "timeline": []
    }
    
    # Convert to Pydantic models
    schedule = convert_legacy_schedule_state(legacy_data)
    print("✅ Converted legacy data to Pydantic models")
    print(f"   Teachers: {len(schedule.teachers)}")
    print(f"   Rooms: {len(schedule.rooms)}")
    print(f"   Sections: {len(schedule.sections)}")
    print(f"   Assignments: {len(schedule.assignments)}")
    
    # Convert back to legacy format
    exported = export_to_legacy_format(schedule)
    print("✅ Exported back to legacy format")
    print(f"   Keys: {list(exported.keys())}")