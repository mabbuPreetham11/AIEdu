import base64
import io
import random
import string

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import LMSException
from app.models.classroom import Classroom, ClassroomMember
from app.models.user import User

INVITE_CODE_LENGTH = 6


class ClassroomService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_classroom(self, teacher: User, name: str) -> Classroom:
        invite_code = await self._generate_unique_invite_code()
        classroom = Classroom(name=name.strip(), teacher_id=teacher.id, invite_code=invite_code)
        self.db.add(classroom)
        await self.db.commit()
        await self.db.refresh(classroom)
        return classroom

    async def list_teacher_classrooms(self, teacher: User) -> list[Classroom]:
        result = await self.db.scalars(select(Classroom).where(Classroom.teacher_id == teacher.id).order_by(Classroom.created_at.desc()))
        return list(result.all())

    async def list_student_classrooms(self, student: User) -> list[tuple[Classroom, ClassroomMember]]:
        result = await self.db.execute(
            select(Classroom, ClassroomMember)
            .join(ClassroomMember, ClassroomMember.classroom_id == Classroom.id)
            .where(ClassroomMember.student_id == student.id)
            .order_by(ClassroomMember.joined_at.desc())
        )
        return list(result.all())

    async def join_by_invite_code(self, student: User, invite_code: str) -> tuple[Classroom, ClassroomMember]:
        normalized_code = invite_code.strip().upper()
        classroom = await self.db.scalar(select(Classroom).where(Classroom.invite_code == normalized_code))
        if not classroom:
            raise LMSException(status_code=404, detail="Invite code not found")
        if classroom.teacher_id == student.id:
            raise LMSException(status_code=400, detail="Teacher cannot join their own classroom as a student")

        existing = await self.db.scalar(
            select(ClassroomMember).where(
                ClassroomMember.classroom_id == classroom.id,
                ClassroomMember.student_id == student.id,
            )
        )
        if existing:
            raise LMSException(status_code=400, detail="You already joined this classroom")

        membership = ClassroomMember(classroom_id=classroom.id, student_id=student.id)
        self.db.add(membership)
        await self.db.commit()
        await self.db.refresh(membership)
        return classroom, membership

    async def _generate_unique_invite_code(self) -> str:
        alphabet = string.ascii_uppercase + string.digits
        for _ in range(20):
            code = "".join(random.choices(alphabet, k=INVITE_CODE_LENGTH))
            exists = await self.db.scalar(select(Classroom.id).where(Classroom.invite_code == code))
            if not exists:
                return code
        raise LMSException(status_code=500, detail="Unable to generate unique invite code")


def classroom_qr_code_data_url(invite_code: str) -> str:
    try:
        import qrcode
    except ImportError as exc:
        raise LMSException(status_code=500, detail="qrcode library is required. Install dependencies from requirements.txt") from exc

    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(invite_code)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
