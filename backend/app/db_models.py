"""SQLAlchemy ORM models for academic scheduling."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class Thread(Base):
    """Chat thread model."""

    __tablename__ = "threads"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=True)
    thread_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = relationship("ThreadItem", back_populates="thread", cascade="all, delete-orphan")


class ThreadItem(Base):
    """Chat message/item in a thread."""

    __tablename__ = "thread_items"

    id = Column(String, primary_key=True, index=True)
    thread_id = Column(String, ForeignKey("threads.id"), index=True)
    role = Column(String)  # user, assistant, system, tool
    content = Column(Text)
    item_type = Column(String)  # UserMessageItem, TextContentPart, etc.
    item_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    thread = relationship("Thread", back_populates="items")
    tool_calls = relationship("ToolCall", back_populates="item", cascade="all, delete-orphan")


class ToolCall(Base):
    """Tool invocation record."""

    __tablename__ = "tool_calls"

    id = Column(String, primary_key=True, index=True)
    item_id = Column(String, ForeignKey("thread_items.id"), index=True)
    tool_name = Column(String, index=True)
    input_args = Column(JSON)  # Arguments passed to the tool
    output = Column(JSON)  # Tool result/response
    status = Column(String, default="pending")  # pending, success, error
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    item = relationship("ThreadItem", back_populates="tool_calls")


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
    thread_id = Column(String, ForeignKey("threads.id"), nullable=True)  # Link to chat thread
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    thread = relationship("Thread")

