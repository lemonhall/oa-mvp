import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db, require_roles
from backend.app.db.models import ProcessType, User
from backend.app.schemas.process_types import (
    ProcessTypeCreate,
    ProcessTypeOut,
    ProcessTypeUpdate,
)

router = APIRouter(prefix="/api/process-types", tags=["process-types"])


def _out(p: ProcessType) -> ProcessTypeOut:
    try:
        fields = json.loads(p.schema_json or "[]")
    except Exception:
        fields = []
    return ProcessTypeOut(
        id=p.id,
        code=p.code,
        name=p.name,
        description=p.description,
        requires_amount=p.requires_amount,
        is_active=p.is_active,
        fields=fields,
    )


@router.get("", response_model=list[ProcessTypeOut])
def list_process_types(
    db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> list[ProcessTypeOut]:
    items = db.scalars(select(ProcessType).where(ProcessType.is_active.is_(True)).order_by(ProcessType.id.asc())).all()
    return [_out(p) for p in items]


@router.get("/all", response_model=list[ProcessTypeOut])
def list_all_process_types(
    db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))
) -> list[ProcessTypeOut]:
    items = db.scalars(select(ProcessType).order_by(ProcessType.id.asc())).all()
    return [_out(p) for p in items]


@router.post("", response_model=ProcessTypeOut, status_code=201)
def create_process_type(
    body: ProcessTypeCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> ProcessTypeOut:
    existing = db.scalar(select(ProcessType).where(ProcessType.code == body.code))
    if existing is not None:
        raise HTTPException(status_code=400, detail="类型编码已存在")
    p = ProcessType(
        code=body.code,
        name=body.name,
        description=body.description,
        requires_amount=body.requires_amount,
        is_active=body.is_active,
        schema_json=json.dumps([f.model_dump() for f in body.fields], ensure_ascii=False),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return _out(p)


@router.patch("/{process_id}", response_model=ProcessTypeOut)
def update_process_type(
    process_id: int,
    body: ProcessTypeUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> ProcessTypeOut:
    p = db.get(ProcessType, process_id)
    if p is None:
        raise HTTPException(status_code=404, detail="类型不存在")
    patch = body.model_dump(exclude_unset=True)
    if "name" in patch:
        p.name = patch["name"]
    if "description" in patch:
        p.description = patch["description"] or ""
    if "requires_amount" in patch:
        p.requires_amount = bool(patch["requires_amount"])
    if "is_active" in patch:
        p.is_active = bool(patch["is_active"])
    if "fields" in patch and patch["fields"] is not None:
        p.schema_json = json.dumps(patch["fields"], ensure_ascii=False)
    db.add(p)
    db.commit()
    db.refresh(p)
    return _out(p)

