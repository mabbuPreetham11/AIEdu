from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.types import JSONType
from app.models.base import Base, TimestampMixin


class Assignment(Base, TimestampMixin):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    topics_covered: Mapped[list | None] = mapped_column(JSONType)
    assigned_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    weightage: Mapped[float] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    max_score: Mapped[float] = mapped_column(Numeric(7, 2), default=100, nullable=False)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    course = relationship("Course", back_populates="assignments")
    questions = relationship("QuizQuestion", back_populates="assignment", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="assignment", cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id"), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list] = mapped_column(JSONType, nullable=False)
    correct_answer: Mapped[str] = mapped_column(String(255), nullable=False)
    points: Mapped[float] = mapped_column(Numeric(5, 2), default=1, nullable=False)
    order_number: Mapped[int] = mapped_column(Integer, nullable=False)

    assignment = relationship("Assignment", back_populates="questions")


class Submission(Base, TimestampMixin):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    submission_url: Mapped[str | None] = mapped_column(String(500))
    submission_text: Mapped[str | None] = mapped_column(Text)
    quiz_answers: Mapped[dict | None] = mapped_column(JSONType)
    plagiarism_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    plagiarism_report: Mapped[dict | None] = mapped_column(JSONType)

    assignment = relationship("Assignment", back_populates="submissions")
    grades = relationship("Grade", back_populates="submission", cascade="all, delete-orphan")
