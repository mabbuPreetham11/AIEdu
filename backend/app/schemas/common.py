from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    detail: str


class TimestampedSchema(ORMModel):
    created_at: datetime
    updated_at: datetime

