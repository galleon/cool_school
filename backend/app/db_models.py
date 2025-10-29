"""SQLAlchemy ORM models for academic scheduling."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Teacher(Base):
    """Teacher model."""

    __tablename__ = "teachers"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    max_load_hours = Column(Float, default=12.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    qualifications = relationship("TeacherQualification", back_populates="teacher", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="teacher")


class Course(Base):
    """Course model."""

    __tablename__ = "courses"

    id = Column(String, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    name = Column(String)
    credits = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    qualifications = relationship("TeacherQualification", back_populates="course", cascade="all, delete-orphan")
    sections = relationship("Section", back_populates="course", cascade="all, delete-orphan")


class TeacherQualification(Base):
    """Teacher course qualification (M2M relationship)."""

    __tablename__ = "teacher_qualifications"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(String, ForeignKey("teachers.id"), index=True)
    course_id = Column(String, ForeignKey("courses.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    teacher = relationship("Teacher", back_populates="qualifications")
    course = relationship("Course", back_populates="qualifications")


class Room(Base):
    """Room/classroom model."""

    __tablename__ = "rooms"

    id = Column(String, primary_key=True, index=True)
    number = Column(String, unique=True, index=True)
    capacity = Column(Integer, default=30)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assignments = relationship("Assignment", back_populates="room")


class Section(Base):
    """Course section model."""

    __tablename__ = "sections"

    id = Column(String, primary_key=True, index=True)
    course_id = Column(String, ForeignKey("courses.id"), index=True)
    section_number = Column(String)
    enrollment = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    course = relationship("Course", back_populates="sections")
    assignments = relationship("Assignment", back_populates="section", cascade="all, delete-orphan")
    timeslots = relationship("Timeslot", back_populates="section", cascade="all, delete-orphan")


class Timeslot(Base):
    """Class timeslot/meeting time model."""

    __tablename__ = "timeslots"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(String, ForeignKey("sections.id"), index=True)
    day = Column(String)  # MONDAY, TUESDAY, etc.
    start_hour = Column(Float)
    end_hour = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    section = relationship("Section", back_populates="timeslots")


class Assignment(Base):
    """Teacher-section assignment model."""

    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(String, ForeignKey("sections.id"), index=True)
    teacher_id = Column(String, ForeignKey("teachers.id"), nullable=True, index=True)
    room_id = Column(String, ForeignKey("rooms.id"), nullable=True, index=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    section = relationship("Section", back_populates="assignments")
    teacher = relationship("Teacher", back_populates="assignments")
    room = relationship("Room", back_populates="assignments")


class ScheduleChange(Base):
    """Audit log for schedule changes."""

    __tablename__ = "schedule_changes"

    id = Column(Integer, primary_key=True, index=True)
    change_type = Column(String)  # ASSIGN, SWAP, REBALANCE, etc.
    description = Column(Text)
    section_id = Column(String, nullable=True, index=True)
    old_teacher_id = Column(String, nullable=True)
    new_teacher_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
