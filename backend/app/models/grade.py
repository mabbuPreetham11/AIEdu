from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.types import JSONType
from app.models.base import Base, TimestampMixin


class Grade(Base, TimestampMixin):
    __tablename__ = "grades"

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    grade_type: Mapped[str] = mapped_column(String(30), nullable=False)
    score: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    max_score: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    ai_graded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_feedback: Mapped[dict | None] = mapped_column(JSONType)
    improvement_suggestions: Mapped[str | None] = mapped_column(Text)
    focus_areas: Mapped[list | None] = mapped_column(JSONType)
    graded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    is_final: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    submission = relationship("Submission", back_populates="grades")
