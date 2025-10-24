from __future__ import annotations

import copy
from .models import TimeSlot, Teacher, Room, CourseSection, Assignment, ScheduleState
from datetime import datetime, timezone
from typing import Any

try:
    from ortools.linear_solver import pywraplp
except ImportError:
    pywraplp = None


def _now_iso() -> str:
    """Return current time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


class ScheduleManager:
    """Manages teacher-course assignments and timetabling."""

    def __init__(self):
        self.state = ScheduleState()
        self._initialize_sample_data()

    def _initialize_sample_data(self):
        """Create sample university data for testing."""
        # Exact toy_state requested by the user
        teachers = {
            "t_alice": Teacher(
                id="t_alice",
                name="Alice",
                email="alice@university.edu",
                max_load_hours=12.0,
                qualified_courses={"CS101", "CS102"},
                availability=[
                    TimeSlot(day=1, start_hour=8.0, end_hour=17.0),
                    TimeSlot(day=2, start_hour=8.0, end_hour=17.0),
                ],
            ),
            "t_bob": Teacher(
                id="t_bob",
                name="Bob",
                email="bob@university.edu",
                max_load_hours=12.0,
                qualified_courses={"CS101", "CS102"},  # Now Bob can teach CS102 too
                availability=[TimeSlot(day=1, start_hour=9.0, end_hour=15.0)],
            ),
            "t_chen": Teacher(
                id="t_chen",
                name="Chen",
                email="chen@university.edu",
                max_load_hours=12.0,
                qualified_courses={"MATH201"},
                availability=[TimeSlot(day=3, start_hour=9.0, end_hour=17.0)],
            ),
        }

        rooms = {
            "r101": Room(id="r101", capacity=30, features={"projector"}),
            "lab1": Room(id="lab1", capacity=20, features={"computers", "projector"}),
        }

        sections = {
            "CS101-A": CourseSection(
                id="CS101-A",
                course_code="CS101",
                timeslots=[TimeSlot(day=1, start_hour=9.0, end_hour=11.0)],
                required_feature="projector",
                enrollment=25,
            ),
            "CS101-B": CourseSection(
                id="CS101-B",
                course_code="CS101",
                timeslots=[TimeSlot(day=1, start_hour=11.0, end_hour=13.0)],
                required_feature="projector",
                enrollment=20,
            ),
            "CS102-A": CourseSection(
                id="CS102-A",
                course_code="CS102",
                timeslots=[TimeSlot(day=2, start_hour=9.0, end_hour=11.0)],
                required_feature="computers",
                enrollment=15,
            ),
            "CS102-B": CourseSection(  # New section that will overload Alice
                id="CS102-B",
                course_code="CS102",
                timeslots=[TimeSlot(day=2, start_hour=11.0, end_hour=13.0)],
                required_feature="computers",
                enrollment=18,
            ),
            "CS102-C": CourseSection(  # Another section that will overload Alice
                id="CS102-C",
                course_code="CS102",
                timeslots=[TimeSlot(day=2, start_hour=13.0, end_hour=15.0)],
                required_feature="computers",
                enrollment=12,
            ),
            "MATH201-A": CourseSection(
                id="MATH201-A",
                course_code="MATH201",
                timeslots=[TimeSlot(day=3, start_hour=10.0, end_hour=12.0)],
                enrollment=30,
            ),
        }

        assignments = {
            "CS101-A": Assignment(section_id="CS101-A", teacher_id="t_alice", room_id="r101"),
            "CS101-B": Assignment(
                section_id="CS101-B", teacher_id=None, room_id=None
            ),  # Unassigned initially
            "CS102-A": Assignment(section_id="CS102-A", teacher_id="t_alice", room_id="lab1"),
            "CS102-B": Assignment(
                section_id="CS102-B", teacher_id="t_alice", room_id="lab1"
            ),  # Alice overloaded
            "CS102-C": Assignment(
                section_id="CS102-C", teacher_id="t_alice", room_id="lab1"
            ),  # Alice very overloaded
            # MATH201-A intentionally left unassigned for the toy state
            "MATH201-A": Assignment(section_id="MATH201-A", teacher_id=None, room_id=None),
        }

        # Store in state
        self.state.teachers = teachers
        self.state.rooms = rooms
        self.state.sections = sections
        self.state.assignments = assignments

        self.state.log("Scheduling data loaded", "system")

    def get_state(self) -> dict[str, Any]:
        """Get the current state as a dictionary."""
        return {
            "teachers": {tid: teacher.to_dict() for tid, teacher in self.state.teachers.items()},
            "rooms": {rid: room.to_dict() for rid, room in self.state.rooms.items()},
            "sections": {sid: section.to_dict() for sid, section in self.state.sections.items()},
            "assignments": {
                aid: assignment.to_dict() for aid, assignment in self.state.assignments.items()
            },
            "timeline": self.state.timeline,
        }

    def compute_teacher_load(self, teacher: Teacher) -> float:
        """Calculate the total teaching load for a teacher."""
        total_hours = 0.0
        for assignment in self.state.assignments.values():
            if assignment.teacher_id == teacher.id:
                section = self.state.sections[assignment.section_id]
                total_hours += section.get_credit_hours()
        return total_hours

    def find_overload(self) -> list[tuple[str, float, float]]:
        """Find teachers who are over their maximum load."""
        overloads = []
        for teacher_id, teacher in self.state.teachers.items():
            current_load = self.compute_teacher_load(teacher)
            if current_load > teacher.max_load_hours:
                overloads.append((teacher_id, current_load, teacher.max_load_hours))
        return overloads

    def find_conflicting_assignments(self) -> list[tuple[str, str]]:
        """Find teachers with conflicting time slots."""
        conflicts = []
        teacher_schedules = {}

        for assignment in self.state.assignments.values():
            if assignment.teacher_id:
                section = self.state.sections[assignment.section_id]
                if assignment.teacher_id not in teacher_schedules:
                    teacher_schedules[assignment.teacher_id] = []

                # Check for time conflicts with all timeslots
                for timeslot in section.timeslots:
                    for existing_slot in teacher_schedules[assignment.teacher_id]:
                        if timeslot.day == existing_slot.day and not (
                            timeslot.end_hour <= existing_slot.start_hour
                            or timeslot.start_hour >= existing_slot.end_hour
                        ):
                            conflicts.append((assignment.teacher_id, assignment.section_id))
                            break

                teacher_schedules[assignment.teacher_id].extend(section.timeslots)

        return conflicts

    def teacher_name_to_id(self, name_or_id: str) -> str | None:
        """Convert teacher name or ID to teacher ID."""
        # Try direct ID lookup first
        if name_or_id in self.state.teachers:
            return name_or_id

        # Try name lookup
        for teacher_id, teacher in self.state.teachers.items():
            if teacher.name.lower() == name_or_id.lower():
                return teacher_id

        return None

    def try_swap(
        self, section_id: str, from_teacher_id: str, to_teacher_id: str
    ) -> tuple[bool, str]:
        """Try to swap a section assignment between teachers."""
        if section_id not in self.state.assignments:
            return False, f"Section {section_id} not found"

        if from_teacher_id not in self.state.teachers:
            return False, f"Teacher {from_teacher_id} not found"

        if to_teacher_id not in self.state.teachers:
            return False, f"Teacher {to_teacher_id} not found"

        assignment = self.state.assignments[section_id]
        if assignment.teacher_id != from_teacher_id:
            return False, f"Section {section_id} is not assigned to teacher {from_teacher_id}"

        # Check if the new teacher would be overloaded
        to_teacher = self.state.teachers[to_teacher_id]
        section = self.state.sections[section_id]
        current_load = self.compute_teacher_load(to_teacher)

        if current_load + section.get_credit_hours() > to_teacher.max_load_hours:
            return False, f"Assignment would overload teacher {to_teacher.name}"

        # Check if teacher is qualified for the course
        if section.course_code not in to_teacher.qualified_courses:
            return (
                False,
                f"Teacher {to_teacher.name} is not qualified to teach {section.course_code}",
            )

        # Perform the swap
        assignment.teacher_id = to_teacher_id
        assignment.assigned_at = _now_iso()

        from_teacher_name = self.state.teachers[from_teacher_id].name
        to_teacher_name = self.state.teachers[to_teacher_id].name

        self.state.log(
            f"Swapped {section_id} from {from_teacher_name} to {to_teacher_name}", "assignment"
        )

        return True, "Swap successful"

    def greedy_rebalance(self, max_load_hours: float | None = None) -> ScheduleState:
        """Perform a greedy rebalancing to distribute teaching loads more evenly."""
        # Work directly on current state assignments
        moved_assignments = []

        # Calculate current loads
        teacher_loads = {}
        for teacher_id, teacher in self.state.teachers.items():
            teacher_loads[teacher_id] = self.compute_teacher_load(teacher)

        # Find assignments that can be moved to balance load
        for assignment in self.state.assignments.values():
            if assignment.teacher_id:
                current_teacher = self.state.teachers[assignment.teacher_id]
                current_load = teacher_loads[assignment.teacher_id]
                section = self.state.sections[assignment.section_id]
                section_hours = section.get_credit_hours()

                # Look for a teacher with significantly lower load who can take this section
                best_teacher = None
                best_load_diff = 0

                for teacher_id, teacher in self.state.teachers.items():
                    if (
                        teacher_id != assignment.teacher_id
                        and section.course_code in teacher.qualified_courses
                    ):
                        target_load = teacher_loads[teacher_id]

                        # Check if this would improve balance and not overload target
                        if (
                            target_load + section_hours <= teacher.max_load_hours
                            and current_load - target_load > 2.0
                        ):  # Only move if significant difference
                            load_diff = current_load - target_load
                            if load_diff > best_load_diff:
                                best_teacher = teacher_id
                                best_load_diff = load_diff

                # Make the move if we found a good candidate
                if best_teacher:
                    old_teacher_name = current_teacher.name
                    new_teacher_name = self.state.teachers[best_teacher].name

                    assignment.teacher_id = best_teacher
                    assignment.assigned_at = _now_iso()

                    # Update our tracking
                    teacher_loads[current_teacher.id] -= section_hours
                    teacher_loads[best_teacher] += section_hours

                    moved_assignments.append(
                        {
                            "section": assignment.section_id,
                            "from": old_teacher_name,
                            "to": new_teacher_name,
                            "hours": section_hours,
                        }
                    )

                    self.state.log(
                        f"Rebalanced: moved {assignment.section_id} from {old_teacher_name} to {new_teacher_name}",
                        "assignment",
                    )

        # Return current state (which has been modified)
        return self.state

    def optimal_rebalance(self, max_load_hours: float | None = None) -> ScheduleState:
        """Perform optimal rebalancing using OR-Tools to minimize load variance."""
        # Check if OR-Tools is available
        if pywraplp is None:
            self.state.log("OR-Tools not available, falling back to greedy rebalancing", "system")
            return self.greedy_rebalance(max_load_hours)

        # Create a copy of current state to work with
        new_state = copy.deepcopy(self.state)

        # Create the solver
        solver = pywraplp.Solver.CreateSolver("SCIP")
        if not solver:
            # Fall back to greedy if OR-Tools solver not available
            self.state.log(
                "OR-Tools solver not available, falling back to greedy rebalancing", "system"
            )
            return self.greedy_rebalance(max_load_hours)

        # Get all teachers and sections
        teachers = list(self.state.teachers.keys())
        sections = list(self.state.sections.keys())

        # Handle empty sections case
        if not sections or not teachers:
            return self.state

        # Create decision variables: x[section][teacher] = 1 if section assigned to teacher
        x = {}
        for section_id in sections:
            x[section_id] = {}
            section = self.state.sections[section_id]
            for teacher_id in teachers:
                # Only create variables for qualified teachers
                if section.course_code in self.state.teachers[teacher_id].qualified_courses:
                    x[section_id][teacher_id] = solver.IntVar(
                        0, 1, f"assign_{section_id}_{teacher_id}"
                    )
                else:
                    x[section_id][teacher_id] = solver.IntVar(
                        0, 0, f"assign_{section_id}_{teacher_id}"
                    )  # Force to 0

        # Constraint 1: Each section must be assigned to exactly one teacher
        for section_id in sections:
            section = self.state.sections[section_id]
            qualified_teachers = [
                tid
                for tid in teachers
                if section.course_code in self.state.teachers[tid].qualified_courses
            ]
            if qualified_teachers:  # Only add constraint if there are qualified teachers
                solver.Add(sum(x[section_id][teacher_id] for teacher_id in qualified_teachers) == 1)

        # Constraint 2: Teachers cannot exceed their maximum load
        for teacher_id in teachers:
            teacher = self.state.teachers[teacher_id]
            max_load = max_load_hours if max_load_hours else teacher.max_load_hours
            teacher_load = sum(
                x[section_id][teacher_id] * self.state.sections[section_id].get_credit_hours()
                for section_id in sections
            )
            solver.Add(teacher_load <= max_load)

        # Objective: Minimize load variance (using auxiliary variables)
        # First, calculate total load and number of teachers for average
        total_hours = sum(section.get_credit_hours() for section in self.state.sections.values())
        num_teachers = len(teachers)
        target_load = total_hours / num_teachers

        # Create auxiliary variables for absolute deviations
        deviations = {}
        for teacher_id in teachers:
            deviations[teacher_id] = solver.NumVar(0, solver.infinity(), f"dev_{teacher_id}")
            teacher_load = sum(
                x[section_id][teacher_id] * self.state.sections[section_id].get_credit_hours()
                for section_id in sections
            )
            # |load - target| = deviation
            solver.Add(deviations[teacher_id] >= teacher_load - target_load)
            solver.Add(deviations[teacher_id] >= target_load - teacher_load)

        # Minimize sum of deviations (approximates minimizing variance)
        solver.Minimize(sum(deviations[teacher_id] for teacher_id in teachers))

        # Solve the problem
        status = solver.Solve()

        if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
            # Apply the optimal solution
            for section_id in sections:
                # Ensure assignment exists in new_state
                if section_id not in new_state.assignments:
                    new_state.assignments[section_id] = Assignment(section_id=section_id)

                for teacher_id in teachers:
                    if x[section_id][teacher_id].solution_value() > 0.5:  # Variable is 1
                        old_teacher_id = new_state.assignments[section_id].teacher_id
                        new_state.assignments[section_id].teacher_id = teacher_id
                        new_state.assignments[section_id].assigned_at = _now_iso()

                        if old_teacher_id != teacher_id:
                            old_name = (
                                self.state.teachers[old_teacher_id].name
                                if old_teacher_id
                                else "Unassigned"
                            )
                            new_name = self.state.teachers[teacher_id].name
                            new_state.log(
                                f"OR-Tools rebalanced: moved {section_id} from {old_name} to {new_name}",
                                "assignment",
                            )

            # Update the manager's state
            self.state = new_state
            return new_state
        else:
            # If no feasible solution found, fall back to greedy
            new_state.log("OR-Tools rebalancing failed, falling back to greedy", "system")
            return self.greedy_rebalance(max_load_hours)

    def _compute_load_for_state(self, state: ScheduleState, teacher: Teacher) -> float:
        """Helper to compute teacher load for a given state."""
        total_hours = 0.0
        for assignment in state.assignments.values():
            if assignment.teacher_id == teacher.id:
                section = state.sections[assignment.section_id]
                total_hours += section.get_credit_hours()
        return total_hours


# Global instance
SCHEDULE_MANAGER = ScheduleManager()
