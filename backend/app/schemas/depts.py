from pydantic import BaseModel, Field


class DeptCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class DeptOut(BaseModel):
    id: int
    name: str
