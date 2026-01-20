from datetime import datetime

from pydantic import BaseModel, Field


class WorkflowCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    request_type: str = Field(pattern="^(leave|reimburse)$")
    is_active: bool = True


class WorkflowUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    is_active: bool | None = None


class WorkflowNodeCreate(BaseModel):
    step_order: int = Field(ge=1, le=100)
    position_id: int
    name: str = Field(default="", max_length=200)


class WorkflowNodeOut(BaseModel):
    id: int
    workflow_id: int
    step_order: int
    position_id: int
    name: str


class WorkflowOut(BaseModel):
    id: int
    name: str
    request_type: str
    is_active: bool
    created_at: datetime
    nodes: list[WorkflowNodeOut] = []

