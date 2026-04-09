from datetime import datetime
from typing import Literal

from pydantic import BaseModel


MaterialTypeLiteral = Literal["pdf", "slide", "video", "link"]


class MaterialRead(BaseModel):
    id: int
    classroom_id: int
    uploader_id: int
    title: str
    type: MaterialTypeLiteral
    file_path: str | None
    url: str | None
    uploaded_at: datetime
    file_url: str | None
