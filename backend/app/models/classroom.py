from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Classroom(Base, TimestampMixin):
    __tablename__ = "classrooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    invite_code: Mapped[str] = mapped_column(String(6), unique=True, nullable=False, index=True)

    teacher = relationship("User", back_populates="classrooms_created")
    members = relationship("ClassroomMember", back_populates="classroom", cascade="all, delete-orphan")
    materials = relationship("Material", back_populates="classroom", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="classroom", cascade="all, delete-orphan")


class ClassroomMember(Base):
    __tablename__ = "classroom_members"

    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id"), primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    classroom = relationship("Classroom", back_populates="members")
    student = relationship("User", back_populates="joined_classrooms")
