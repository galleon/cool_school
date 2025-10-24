"""Tests for the OR-Tools based rebalancing functionality."""

from app.schedule_state import Assignment, CourseSection, Room, ScheduleManager, Teacher, TimeSlot


class TestRebalancing:
    """Test suite for OR-Tools optimal rebalancing."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.manager = ScheduleManager()

    def create_unbalanced_scenario(self):
        """Create a scenario where rebalancing is needed."""
        # Clear existing state
        self.manager.state.teachers.clear()
        self.manager.state.sections.clear()
        self.manager.state.assignments.clear()
        self.manager.state.rooms.clear()
        self.manager.state.timeline.clear()

        # Create teachers with different qualifications
        self.manager.state.teachers = {
            "t_alice": Teacher(
                id="t_alice",
                name="Alice",
                email="alice@university.edu",
                max_load_hours=8.0,
                qualified_courses={"CS101", "CS102"},
            ),
            "t_bob": Teacher(
                id="t_bob",
                name="Bob",
                email="bob@university.edu",
                max_load_hours=8.0,
                qualified_courses={"CS101", "CS102"},
            ),
            "t_chen": Teacher(
                id="t_chen",
                name="Chen",
                email="chen@university.edu",
                max_load_hours=6.0,
                qualified_courses={"MATH201"},
            ),
        }

        # Create rooms
        self.manager.state.rooms = {
            "r101": Room(id="r101", capacity=30, features={"projector"}),
            "lab1": Room(id="lab1", capacity=20, features={"computers"}),
        }

        # Create course sections
        self.manager.state.sections = {
            "CS101-A": CourseSection(
                id="CS101-A",
                course_code="CS101",
                timeslots=[TimeSlot(day=1, start_hour=9.0, end_hour=11.0)],  # 2 hours
                enrollment=25,
            ),
            "CS101-B": CourseSection(
                id="CS101-B",
                course_code="CS101",
                timeslots=[TimeSlot(day=1, start_hour=11.0, end_hour=13.0)],  # 2 hours
                enrollment=20,
            ),
            "CS102-A": CourseSection(
                id="CS102-A",
                course_code="CS102",
                timeslots=[TimeSlot(day=2, start_hour=9.0, end_hour=11.0)],  # 2 hours
                enrollment=15,
            ),
            "CS102-B": CourseSection(
                id="CS102-B",
                course_code="CS102",
                timeslots=[TimeSlot(day=2, start_hour=11.0, end_hour=13.0)],  # 2 hours
                enrollment=18,
            ),
            "MATH201-A": CourseSection(
                id="MATH201-A",
                course_code="MATH201",
                timeslots=[TimeSlot(day=3, start_hour=10.0, end_hour=12.0)],  # 2 hours
                enrollment=30,
            ),
        }

        # Create unbalanced assignments: Alice gets overloaded, Bob gets nothing
        self.manager.state.assignments = {
            "CS101-A": Assignment(section_id="CS101-A", teacher_id="t_alice", room_id="r101"),
            "CS101-B": Assignment(section_id="CS101-B", teacher_id="t_alice", room_id="r101"),
            "CS102-A": Assignment(section_id="CS102-A", teacher_id="t_alice", room_id="lab1"),
            "CS102-B": Assignment(
                section_id="CS102-B", teacher_id="t_alice", room_id="lab1"
            ),  # Alice: 8 hours total
            "MATH201-A": Assignment(
                section_id="MATH201-A", teacher_id="t_chen", room_id="r101"
            ),  # Chen: 2 hours
            # Bob gets nothing (0 hours)
        }

    def test_compute_teacher_loads_before_rebalancing(self):
        """Test that we can compute teacher loads correctly."""
        self.create_unbalanced_scenario()

        alice = self.manager.state.teachers["t_alice"]
        bob = self.manager.state.teachers["t_bob"]
        chen = self.manager.state.teachers["t_chen"]

        alice_load = self.manager.compute_teacher_load(alice)
        bob_load = self.manager.compute_teacher_load(bob)
        chen_load = self.manager.compute_teacher_load(chen)

        # Alice should have 8 hours (4 sections × 2 hours each)
        assert alice_load == 8.0, f"Alice should have 8 hours, got {alice_load}"

        # Bob should have 0 hours
        assert bob_load == 0.0, f"Bob should have 0 hours, got {bob_load}"

        # Chen should have 2 hours
        assert chen_load == 2.0, f"Chen should have 2 hours, got {chen_load}"

    def test_optimal_rebalancing_improves_balance(self):
        """Test that OR-Tools rebalancing improves load distribution."""
        self.create_unbalanced_scenario()

        # Get initial loads
        alice = self.manager.state.teachers["t_alice"]
        bob = self.manager.state.teachers["t_bob"]
        chen = self.manager.state.teachers["t_chen"]

        initial_alice_load = self.manager.compute_teacher_load(alice)
        initial_bob_load = self.manager.compute_teacher_load(bob)
        initial_chen_load = self.manager.compute_teacher_load(chen)

        # Calculate initial variance
        loads = [initial_alice_load, initial_bob_load, initial_chen_load]
        mean_load = sum(loads) / len(loads)
        initial_variance = sum((load - mean_load) ** 2 for load in loads) / len(loads)

        # Run optimal rebalancing
        self.manager.optimal_rebalance()

        # Get final loads
        final_alice_load = self.manager.compute_teacher_load(alice)
        final_bob_load = self.manager.compute_teacher_load(bob)
        final_chen_load = self.manager.compute_teacher_load(chen)

        # Calculate final variance
        final_loads = [final_alice_load, final_bob_load, final_chen_load]
        final_mean_load = sum(final_loads) / len(final_loads)
        final_variance = sum((load - final_mean_load) ** 2 for load in final_loads) / len(
            final_loads
        )

        # Rebalancing should reduce variance (better distribution)
        assert final_variance <= initial_variance, (
            f"Variance should decrease: {initial_variance} -> {final_variance}"
        )

        # All teachers should respect their max load constraints
        assert final_alice_load <= alice.max_load_hours, (
            f"Alice overloaded: {final_alice_load} > {alice.max_load_hours}"
        )
        assert final_bob_load <= bob.max_load_hours, (
            f"Bob overloaded: {final_bob_load} > {bob.max_load_hours}"
        )
        assert final_chen_load <= chen.max_load_hours, (
            f"Chen overloaded: {final_chen_load} > {chen.max_load_hours}"
        )

        # Total hours should be conserved
        initial_total = initial_alice_load + initial_bob_load + initial_chen_load
        final_total = final_alice_load + final_bob_load + final_chen_load
        assert abs(initial_total - final_total) < 0.1, (
            f"Total hours not conserved: {initial_total} -> {final_total}"
        )

    def test_rebalancing_respects_qualifications(self):
        """Test that rebalancing only assigns sections to qualified teachers."""
        self.create_unbalanced_scenario()

        # Run rebalancing
        self.manager.optimal_rebalance()

        # Check that every assignment respects qualifications
        for assignment_id, assignment in self.manager.state.assignments.items():
            if assignment.teacher_id:
                section = self.manager.state.sections[assignment.section_id]
                teacher = self.manager.state.teachers[assignment.teacher_id]

                assert section.course_code in teacher.qualified_courses, (
                    f"Section {assignment.section_id} ({section.course_code}) assigned to unqualified "
                    f"teacher {teacher.name} (qualified: {teacher.qualified_courses})"
                )

    def test_rebalancing_with_max_load_constraint(self):
        """Test rebalancing with a custom max load hours constraint."""
        self.create_unbalanced_scenario()

        # Set a lower max load constraint (4 hours for everyone)
        custom_max_load = 4.0

        # Run rebalancing with constraint
        self.manager.optimal_rebalance(max_load_hours=custom_max_load)

        # Check that no teacher exceeds the custom constraint
        for teacher_id, teacher in self.manager.state.teachers.items():
            load = self.manager.compute_teacher_load(teacher)
            assert load <= custom_max_load, (
                f"Teacher {teacher.name} exceeds custom max load: {load} > {custom_max_load}"
            )

    def test_empty_state_rebalancing(self):
        """Test rebalancing with no assignments."""
        # Clear all assignments and sections
        self.manager.state.assignments.clear()
        self.manager.state.sections.clear()

        # Rebalancing should not crash
        result_state = self.manager.optimal_rebalance()

        # Should return the same (empty) state
        assert len(result_state.assignments) == 0
        assert len(result_state.sections) == 0

    def test_already_balanced_state(self):
        """Test rebalancing when assignments are already balanced."""
        # Create a balanced scenario
        self.manager.state.teachers.clear()
        self.manager.state.sections.clear()
        self.manager.state.assignments.clear()

        # Create teachers
        self.manager.state.teachers = {
            "t_alice": Teacher(
                id="t_alice",
                name="Alice",
                email="alice@university.edu",
                max_load_hours=4.0,
                qualified_courses={"CS101"},
            ),
            "t_bob": Teacher(
                id="t_bob",
                name="Bob",
                email="bob@university.edu",
                max_load_hours=4.0,
                qualified_courses={"CS101"},
            ),
        }

        # Create sections
        self.manager.state.sections = {
            "CS101-A": CourseSection(
                id="CS101-A",
                course_code="CS101",
                timeslots=[TimeSlot(day=1, start_hour=9.0, end_hour=11.0)],
                enrollment=25,
            ),
            "CS101-B": CourseSection(
                id="CS101-B",
                course_code="CS101",
                timeslots=[TimeSlot(day=1, start_hour=11.0, end_hour=13.0)],
                enrollment=20,
            ),
        }

        # Create balanced assignments (2 hours each)
        self.manager.state.assignments = {
            "CS101-A": Assignment(section_id="CS101-A", teacher_id="t_alice"),
            "CS101-B": Assignment(section_id="CS101-B", teacher_id="t_bob"),
        }

        # Run rebalancing
        self.manager.optimal_rebalance()

        # Assignments might change but loads should remain balanced
        alice_load = self.manager.compute_teacher_load(self.manager.state.teachers["t_alice"])
        bob_load = self.manager.compute_teacher_load(self.manager.state.teachers["t_bob"])

        # Both should have 2 hours (or close to it)
        assert abs(alice_load - bob_load) <= 2.0, (
            f"Loads not balanced: Alice {alice_load}, Bob {bob_load}"
        )
