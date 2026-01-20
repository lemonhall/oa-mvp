from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=200)
    full_name: str = ""
    role: str = "employee"
    department_id: int | None = None


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool
    department_id: int | None


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    department_id: int | None = None
    is_active: bool | None = None
