from datetime import datetime

from pydantic import BaseModel, Field


class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = ""


class AnnouncementOut(BaseModel):
    id: int
    title: str
    content: str
    created_by_user_id: int
    created_at: datetime
