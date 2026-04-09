import re
import secrets
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import LMSException
from app.models.classroom import Classroom, ClassroomMember
from app.models.material import Material, MaterialType
from app.models.user import User, UserRole
from app.services.rag_service import RAGService

HTTP_URL_RE = re.compile(r"^https?://", re.IGNORECASE)
YOUTUBE_RE = re.compile(r"(youtube\.com|youtu\.be)", re.IGNORECASE)


class MaterialService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.base_upload_dir = Path(settings.local_storage_path)
        self.rag_service = RAGService()

    async def list_for_classroom(self, classroom_id: int, user: User) -> list[Material]:
        classroom = await self._get_classroom_or_404(classroom_id)
        await self._ensure_view_permission(classroom, user)
        result = await self.db.scalars(
            select(Material).where(Material.classroom_id == classroom_id).order_by(Material.uploaded_at.desc())
        )
        return list(result.all())

    async def create_material(
        self,
        classroom_id: int,
        teacher: User,
        title: str,
        material_type: str,
        url: str | None,
        file: UploadFile | None,
    ) -> Material:
        classroom = await self._get_classroom_or_404(classroom_id)
        if teacher.role != UserRole.teacher:
            raise LMSException(status_code=403, detail="Only teachers can upload material")
        if classroom.teacher_id != teacher.id:
            raise LMSException(status_code=403, detail="Only classroom teacher can upload material")

        normalized_type = material_type.strip().lower()
        if normalized_type not in {"pdf", "slide", "video", "link"}:
            raise LMSException(status_code=400, detail="Invalid material type")

        kind = MaterialType(normalized_type)
        cleaned_title = title.strip()
        if not cleaned_title:
            raise LMSException(status_code=400, detail="Title is required")

        file_path: str | None = None
        normalized_url: str | None = url.strip() if url else None

        if kind in {MaterialType.pdf, MaterialType.slide}:
            if not file:
                raise LMSException(status_code=400, detail="PDF file is required for pdf/slide material")
            if not file.filename or not file.filename.lower().endswith(".pdf"):
                raise LMSException(status_code=400, detail="Only PDF files are supported for pdf/slide material")
            key = await self._save_file(classroom_id, file)
            file_path = key
            normalized_url = None
        else:
            if not normalized_url:
                raise LMSException(status_code=400, detail="URL is required for video/link material")
            if not HTTP_URL_RE.match(normalized_url):
                raise LMSException(status_code=400, detail="URL must start with http:// or https://")
            if kind == MaterialType.video and not YOUTUBE_RE.search(normalized_url):
                raise LMSException(status_code=400, detail="Video link must be a YouTube URL")
            file_path = None

        material = Material(
            classroom_id=classroom_id,
            uploader_id=teacher.id,
            title=cleaned_title,
            type=kind,
            file_path=file_path,
            url=normalized_url,
        )
        self.db.add(material)
        await self.db.commit()
        await self.db.refresh(material)

        if material.type in {MaterialType.pdf, MaterialType.slide} and material.file_path:
            absolute_path = self.base_upload_dir / material.file_path
            self.rag_service.index_pdf(
                classroom_id=classroom_id,
                material_id=material.id,
                doc_name=material.title,
                file_path=absolute_path,
            )
        return material

    async def get_material_for_download(self, classroom_id: int, material_id: int, user: User) -> Material:
        classroom = await self._get_classroom_or_404(classroom_id)
        await self._ensure_view_permission(classroom, user)
        material = await self.db.scalar(
            select(Material).where(Material.id == material_id, Material.classroom_id == classroom_id)
        )
        if not material:
            raise LMSException(status_code=404, detail="Material not found")
        if material.type not in {MaterialType.pdf, MaterialType.slide} or not material.file_path:
            raise LMSException(status_code=400, detail="This material is not downloadable as a file")
        return material

    async def _get_classroom_or_404(self, classroom_id: int) -> Classroom:
        classroom = await self.db.scalar(select(Classroom).where(Classroom.id == classroom_id))
        if not classroom:
            raise LMSException(status_code=404, detail="Classroom not found")
        return classroom

    async def _ensure_view_permission(self, classroom: Classroom, user: User) -> None:
        if user.role == UserRole.teacher and classroom.teacher_id == user.id:
            return
        if user.role == UserRole.student:
            membership = await self.db.scalar(
                select(ClassroomMember).where(
                    ClassroomMember.classroom_id == classroom.id, ClassroomMember.student_id == user.id
                )
            )
            if membership:
                return
        raise LMSException(status_code=403, detail="Not allowed to access this classroom material")

    async def _save_file(self, classroom_id: int, file: UploadFile) -> str:
        content = await file.read()
        safe_name = f"{secrets.token_hex(6)}.pdf"
        relative_key = f"classroom-materials/{classroom_id}/{safe_name}"
        destination = self.base_upload_dir / relative_key
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        return relative_key.replace("\\", "/")
