from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, require_roles
from backend.app.db.models import Department, User
from backend.app.schemas.depts import DeptCreate, DeptOut

router = APIRouter(prefix="/api/depts", tags=["depts"])


@router.get("", response_model=list[DeptOut])
def list_depts(db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    items = db.scalars(select(Department).order_by(Department.id)).all()
    return [DeptOut(id=d.id, name=d.name) for d in items]


@router.post("", response_model=DeptOut, status_code=201)
def create_dept(
    body: DeptCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> DeptOut:
    existing = db.scalar(select(Department).where(Department.name == body.name))
    if existing is not None:
        raise HTTPException(status_code=400, detail="Department already exists")

    dept = Department(name=body.name)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return DeptOut(id=dept.id, name=dept.name)
