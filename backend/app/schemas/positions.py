from pydantic import BaseModel, Field


class PositionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""


class PositionOut(BaseModel):
    id: int
    name: str
    description: str

