from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, require_roles
from backend.app.db.models import Position, User, Workflow, WorkflowNode
from backend.app.schemas.workflows import (
    WorkflowCreate,
    WorkflowNodeCreate,
    WorkflowNodeOut,
    WorkflowOut,
    WorkflowUpdate,
)

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


def _node_out(n: WorkflowNode) -> WorkflowNodeOut:
    return WorkflowNodeOut(
        id=n.id,
        workflow_id=n.workflow_id,
        step_order=n.step_order,
        position_id=n.position_id,
        name=n.name,
    )


def _workflow_out(db: Session, wf: Workflow) -> WorkflowOut:
    nodes = db.scalars(
        select(WorkflowNode)
        .where(WorkflowNode.workflow_id == wf.id)
        .order_by(WorkflowNode.step_order.asc())
    ).all()
    return WorkflowOut(
        id=wf.id,
        name=wf.name,
        request_type=wf.request_type,
        is_active=wf.is_active,
        created_at=wf.created_at,
        nodes=[_node_out(n) for n in nodes],
    )


@router.get("", response_model=list[WorkflowOut])
def list_workflows(
    request_type: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> list[WorkflowOut]:
    q = select(Workflow).order_by(Workflow.id.asc())
    if request_type:
        q = q.where(Workflow.request_type == request_type)
    items = db.scalars(q).all()
    return [_workflow_out(db, wf) for wf in items]


@router.post("", response_model=WorkflowOut, status_code=201)
def create_workflow(
    body: WorkflowCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> WorkflowOut:
    existing = db.scalar(select(Workflow).where(Workflow.name == body.name))
    if existing is not None:
        raise HTTPException(status_code=400, detail="Workflow name already exists")
    wf = Workflow(name=body.name, request_type=body.request_type, is_active=body.is_active)
    db.add(wf)
    db.commit()
    db.refresh(wf)
    return _workflow_out(db, wf)


@router.get("/{workflow_id}", response_model=WorkflowOut)
def get_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> WorkflowOut:
    wf = db.get(Workflow, workflow_id)
    if wf is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _workflow_out(db, wf)


@router.patch("/{workflow_id}", response_model=WorkflowOut)
def update_workflow(
    workflow_id: int,
    body: WorkflowUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> WorkflowOut:
    wf = db.get(Workflow, workflow_id)
    if wf is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if body.name is not None:
        wf.name = body.name
    if body.is_active is not None:
        wf.is_active = body.is_active
    db.add(wf)
    db.commit()
    db.refresh(wf)
    return _workflow_out(db, wf)


@router.post("/{workflow_id}/nodes", response_model=WorkflowNodeOut, status_code=201)
def add_node(
    workflow_id: int,
    body: WorkflowNodeCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> WorkflowNodeOut:
    wf = db.get(Workflow, workflow_id)
    if wf is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    pos = db.get(Position, body.position_id)
    if pos is None:
        raise HTTPException(status_code=404, detail="Position not found")

    existing = db.scalar(
        select(WorkflowNode)
        .where(WorkflowNode.workflow_id == workflow_id)
        .where(WorkflowNode.step_order == body.step_order)
    )
    if existing is not None:
        raise HTTPException(status_code=400, detail="step_order already exists")

    node = WorkflowNode(
        workflow_id=workflow_id,
        step_order=body.step_order,
        position_id=body.position_id,
        name=body.name,
    )
    db.add(node)
    db.commit()
    db.refresh(node)
    return _node_out(node)


@router.delete("/{workflow_id}/nodes/{node_id}", status_code=204)
def delete_node(
    workflow_id: int,
    node_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> None:
    node = db.get(WorkflowNode, node_id)
    if node is None or node.workflow_id != workflow_id:
        raise HTTPException(status_code=404, detail="Node not found")
    db.delete(node)
    db.commit()

