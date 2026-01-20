from datetime import datetime

from pydantic import BaseModel, Field


class RequestCreate(BaseModel):
    type: str = Field(pattern="^(leave|reimburse)$")
    title: str = Field(min_length=1, max_length=200)
    content: str = ""
    amount: float | None = None


class RequestOut(BaseModel):
    id: int
    type: str
    title: str
    content: str
    amount: float | None
    status: str
    created_by_user_id: int
    approver_user_id: int | None
    created_at: datetime
    updated_at: datetime


class ApprovalDecision(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")
    comment: str = ""
