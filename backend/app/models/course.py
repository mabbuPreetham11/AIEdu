from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.types import JSONType
from app.models.base import Base, TimestampMixin


class Course(Base, TimestampMixin):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_code: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    class_code: Mapped[str] = mapped_column(String(16), unique=True, index=True, nullable=False)
    course_info_url: Mapped[str | None] = mapped_column(String(500))
    syllabus: Mapped[dict | None] = mapped_column(JSONType)
    grading_weights: Mapped[dict | None] = mapped_column(JSONType)
    semester: Mapped[str] = mapped_column(String(30), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    teacher = relationship("User", back_populates="taught_courses")
    enrollments = relationship("CourseEnrollment", back_populates="course", cascade="all, delete-orphan")
    sessions = relationship("ClassSession", back_populates="course", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="course", cascade="all, delete-orphan")
    announcements = relationship("Announcement", back_populates="course", cascade="all, delete-orphan")


class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    enrollment_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)

    course = relationship("Course", back_populates="enrollments")


class ClassSession(Base, TimestampMixin):
    __tablename__ = "class_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    session_number: Mapped[int] = mapped_column(Integer, nullable=False)
    topics_covered: Mapped[str] = mapped_column(Text, nullable=False)
    session_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)

    course = relationship("Course", back_populates="sessions")
    notes = relationship("SessionNote", back_populates="session", cascade="all, delete-orphan")


class SessionNote(Base, TimestampMixin):
    __tablename__ = "session_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("class_sessions.id"), nullable=False)
    student_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    session = relationship("ClassSession", back_populates="notes")


class Announcement(Base, TimestampMixin):
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    course = relationship("Course", back_populates="announcements")
