from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, require_roles
from backend.app.db.models import Position, User
from backend.app.schemas.positions import PositionCreate, PositionOut

router = APIRouter(prefix="/api/positions", tags=["positions"])


@router.get("", response_model=list[PositionOut])
def list_positions(
    db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))
) -> list[PositionOut]:
    items = db.scalars(select(Position).order_by(Position.id.asc())).all()
    return [PositionOut(id=p.id, name=p.name, description=p.description) for p in items]


@router.post("", response_model=PositionOut, status_code=201)
def create_position(
    body: PositionCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> PositionOut:
    existing = db.scalar(select(Position).where(Position.name == body.name))
    if existing is not None:
        raise HTTPException(status_code=400, detail="Position already exists")
    p = Position(name=body.name, description=body.description)
    db.add(p)
    db.commit()
    db.refresh(p)
    return PositionOut(id=p.id, name=p.name, description=p.description)

