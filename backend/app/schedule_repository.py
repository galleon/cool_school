"""Repository for persisting schedule state to PostgreSQL."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.db_models import (
    Assignment as AssignmentDB,
    Course as CourseDB,
    Room as RoomDB,
    ScheduleChange as ScheduleChangeDB,
    Section as SectionDB,
    Teacher as TeacherDB,
    TeacherQualification as TeacherQualificationDB,
)
from app.models import (
    Assignment,
    CourseSection,
    Room,
    ScheduleState,
    Teacher,
    TimeSlot,
)


class ScheduleRepository:
    """Repository for schedule persistence."""

    def __init__(self, db: Session):
        self.db = db

    def load_schedule_state(self) -> ScheduleState | None:
        """Load schedule state from database, or None if empty."""
        teachers_db = self.db.query(TeacherDB).all()
        if not teachers_db:
            return None

        # Load teachers with qualifications
        teachers = {}
        for t_db in teachers_db:
            qualified_courses = {q.course.code for q in t_db.qualifications}
            teacher = Teacher(
                id=t_db.id,
                name=t_db.name,
                email=t_db.email,
                max_load_hours=t_db.max_load_hours,
                qualified_courses=qualified_courses,
                availability=[],  # TODO: load from availability table if added
            )
            teachers[t_db.id] = teacher

        # Load rooms
        rooms = {}
        for r_db in self.db.query(RoomDB).all():
            room = Room(
                id=r_db.id,
                capacity=r_db.capacity,
                features=set(),  # TODO: load features from features table if added
            )
            rooms[r_db.id] = room

        # Load sections with timeslots and assignments
        sections = {}
        assignments = {}

        for s_db in self.db.query(SectionDB).all():
            timeslots = [
                TimeSlot(
                    day=int(ts.day),
                    start_hour=ts.start_hour,
                    end_hour=ts.end_hour,
                )
                for ts in s_db.timeslots
            ]
            
            section = CourseSection(
                id=s_db.id,
                course_code=s_db.course.code,
                timeslots=timeslots,
                required_feature=None,  # TODO: add to database schema
                enrollment=s_db.enrollment,
            )
            sections[s_db.id] = section

            # Load assignments for this section
            for a_db in s_db.assignments:
                assignment = Assignment(
                    section_id=a_db.section_id,
                    teacher_id=a_db.teacher_id,
                    room_id=a_db.room_id,
                    assigned_at=a_db.assigned_at.isoformat() if a_db.assigned_at else None,
                )
                assignments[s_db.id] = assignment

        # Build schedule state
        state = ScheduleState()
        state.teachers = teachers
        state.rooms = rooms
        state.sections = sections
        state.assignments = assignments

        return state

    def save_teacher(self, teacher: Teacher) -> None:
        """Save or update teacher."""
        existing = self.db.query(TeacherDB).filter(TeacherDB.id == teacher.id).first()

        if existing:
            existing.name = teacher.name
            existing.email = teacher.email
            existing.max_load_hours = teacher.max_load_hours
            existing.updated_at = datetime.utcnow()
        else:
            db_teacher = TeacherDB(
                id=teacher.id,
                name=teacher.name,
                email=teacher.email,
                max_load_hours=teacher.max_load_hours,
            )
            self.db.add(db_teacher)

        # Update qualifications
        self.db.query(TeacherQualificationDB).filter(
            TeacherQualificationDB.teacher_id == teacher.id
        ).delete()

        for course_code in teacher.qualified_courses:
            course = self.db.query(CourseDB).filter(CourseDB.code == course_code).first()
            if course:
                qual = TeacherQualificationDB(
                    teacher_id=teacher.id,
                    course_id=course.id,
                )
                self.db.add(qual)

        self.db.commit()

    def save_assignment(self, assignment: Assignment) -> None:
        """Save or update assignment."""
        existing = self.db.query(AssignmentDB).filter(
            AssignmentDB.section_id == assignment.section_id
        ).first()

        if existing:
            existing.teacher_id = assignment.teacher_id
            existing.room_id = assignment.room_id
            existing.assigned_at = datetime.fromisoformat(
                assignment.assigned_at
            ) if assignment.assigned_at else datetime.utcnow()
            existing.updated_at = datetime.utcnow()
        else:
            db_assignment = AssignmentDB(
                section_id=assignment.section_id,
                teacher_id=assignment.teacher_id,
                room_id=assignment.room_id,
                assigned_at=datetime.fromisoformat(
                    assignment.assigned_at
                ) if assignment.assigned_at else datetime.utcnow(),
            )
            self.db.add(db_assignment)

        self.db.commit()

    def record_change(self, change_type: str, description: str, section_id: str | None = None,
                      old_teacher_id: str | None = None, new_teacher_id: str | None = None) -> None:
        """Record a schedule change in the audit log."""
        change = ScheduleChangeDB(
            change_type=change_type,
            description=description,
            section_id=section_id,
            old_teacher_id=old_teacher_id,
            new_teacher_id=new_teacher_id,
        )
        self.db.add(change)
        self.db.commit()
