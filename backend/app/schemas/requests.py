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
    workflow_id: int | None
    current_node_id: int | None
    created_by_user_id: int
    approver_user_id: int | None
    created_at: datetime
    updated_at: datetime


class ApprovalDecision(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")
    comment: str = ""


class RequestNodeStatus(BaseModel):
    node_id: int
    step_order: int
    node_name: str
    position_id: int
    position_name: str
    status: str = Field(pattern="^(approved|rejected|pending|not_started)$")
    decided_by_user_id: int | None = None
    decided_by_username: str | None = None
    decided_at: datetime | None = None
    comment: str | None = None


class ApprovalHistoryItem(BaseModel):
    id: int
    workflow_node_id: int | None
    step_order: int | None
    node_name: str | None
    position_id: int | None
    position_name: str | None
    approver_user_id: int
    approver_username: str
    decision: str
    comment: str
    decided_at: datetime


class RequestDetail(BaseModel):
    request: RequestOut
    workflow_name: str | None = None
    nodes: list[RequestNodeStatus] = []
    history: list[ApprovalHistoryItem] = []
