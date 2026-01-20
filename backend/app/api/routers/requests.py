from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.db.models import OARequest, User, Workflow, WorkflowNode
from backend.app.schemas.requests import RequestCreate, RequestOut

router = APIRouter(prefix="/api/requests", tags=["requests"])


def _get_active_workflow(db: Session, request_type: str) -> Workflow | None:
    return db.scalar(
        select(Workflow)
        .where(Workflow.request_type == request_type)
        .where(Workflow.is_active.is_(True))
        .order_by(Workflow.id.asc())
    )


def _get_first_node(db: Session, workflow_id: int) -> WorkflowNode | None:
    return db.scalar(
        select(WorkflowNode)
        .where(WorkflowNode.workflow_id == workflow_id)
        .order_by(WorkflowNode.step_order.asc())
    )


def _pick_assignee_by_position(
    db: Session, *, position_id: int, exclude_user_id: int | None = None
) -> int | None:
    q = (
        select(User)
        .where(User.is_active.is_(True))
        .where(User.position_id == position_id)
        .order_by(User.id.asc())
    )
    if exclude_user_id is not None:
        q = q.where(User.id != exclude_user_id)
    u = db.scalar(q)
    return u.id if u else None


@router.post("", response_model=RequestOut, status_code=201)
def create_request(
    body: RequestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RequestOut:
    if body.type == "reimburse" and body.amount is None:
        raise HTTPException(status_code=400, detail="amount is required for reimburse")

    wf = _get_active_workflow(db, body.type)
    if wf is None:
        raise HTTPException(status_code=400, detail="No active workflow for this type")
    first_node = _get_first_node(db, wf.id)
    if first_node is None:
        raise HTTPException(status_code=400, detail="Workflow has no nodes")

    approver_id = _pick_assignee_by_position(
        db, position_id=first_node.position_id, exclude_user_id=user.id
    )
    req = OARequest(
        type=body.type,
        title=body.title,
        content=body.content,
        amount=body.amount,
        status="pending",
        workflow_id=wf.id,
        current_node_id=first_node.id,
        created_by_user_id=user.id,
        approver_user_id=approver_id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return RequestOut(
        id=req.id,
        type=req.type,
        title=req.title,
        content=req.content,
        amount=req.amount,
        status=req.status,
        workflow_id=req.workflow_id,
        current_node_id=req.current_node_id,
        created_by_user_id=req.created_by_user_id,
        approver_user_id=req.approver_user_id,
        created_at=req.created_at,
        updated_at=req.updated_at,
    )


@router.get("/mine", response_model=list[RequestOut])
def list_my_requests(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[RequestOut]:
    items = db.scalars(
        select(OARequest)
        .where(OARequest.created_by_user_id == user.id)
        .order_by(OARequest.id.desc())
    ).all()
    return [
        RequestOut(
            id=r.id,
            type=r.type,
            title=r.title,
            content=r.content,
            amount=r.amount,
            status=r.status,
            workflow_id=r.workflow_id,
            current_node_id=r.current_node_id,
            created_by_user_id=r.created_by_user_id,
            approver_user_id=r.approver_user_id,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in items
    ]


@router.get("/{request_id}", response_model=RequestOut)
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RequestOut:
    r = db.get(OARequest, request_id)
    if r is None:
        raise HTTPException(status_code=404, detail="Request not found")
    is_current_approver = False
    if r.current_node_id is not None and user.position_id is not None:
        node = db.get(WorkflowNode, r.current_node_id)
        if node is not None and node.position_id == user.position_id:
            is_current_approver = True

    if (
        user.role != "admin"
        and r.created_by_user_id != user.id
        and not is_current_approver
    ):
        raise HTTPException(status_code=403, detail="Not allowed")
    return RequestOut(
        id=r.id,
        type=r.type,
        title=r.title,
        content=r.content,
        amount=r.amount,
        status=r.status,
        workflow_id=r.workflow_id,
        current_node_id=r.current_node_id,
        created_by_user_id=r.created_by_user_id,
        approver_user_id=r.approver_user_id,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )
