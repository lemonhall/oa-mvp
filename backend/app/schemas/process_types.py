from typing import Any

from pydantic import BaseModel, Field


class ProcessField(BaseModel):
    key: str = Field(min_length=1, max_length=50)
    label: str = Field(min_length=1, max_length=100)
    type: str = Field(pattern="^(text|textarea|number|date|datetime|select)$")
    required: bool = False
    options: list[str] | None = None


class ProcessTypeOut(BaseModel):
    id: int
    code: str
    name: str
    description: str
    requires_amount: bool
    is_active: bool
    fields: list[ProcessField] = []


class ProcessTypeCreate(BaseModel):
    code: str = Field(pattern="^[a-z][a-z0-9_]{1,49}$")
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    requires_amount: bool = False
    is_active: bool = True
    fields: list[ProcessField] = []


class ProcessTypeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    requires_amount: bool | None = None
    is_active: bool | None = None
    fields: list[ProcessField] | None = None


class ProcessData(BaseModel):
    data: dict[str, Any] = {}

