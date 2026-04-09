from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.user import User, UserRole


async def seed_demo_data() -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.scalar(select(User).limit(1))
        if existing:
            return

        users = [
            User(
                email="teacher@iiitdwd.ac.in",
                password_hash=get_password_hash("Teacher123!"),
                role=UserRole.teacher,
                first_name="Demo",
                last_name="Teacher",
                is_active=True,
                is_verified=True,
            ),
            User(
                email="student@iiitdwd.ac.in",
                password_hash=get_password_hash("Student123!"),
                role=UserRole.student,
                first_name="Demo",
                last_name="Student",
                is_active=True,
                is_verified=True,
            ),
        ]
        session.add_all(users)
        await session.commit()
