from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.db.models import Approval, OARequest, User, WorkflowNode
from backend.app.schemas.requests import ApprovalDecision, RequestOut

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


@router.get("/pending", response_model=list[RequestOut])
def list_pending(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[RequestOut]:
    q = (
        select(OARequest)
        .join(WorkflowNode, OARequest.current_node_id == WorkflowNode.id)
        .where(OARequest.status == "pending")
        .order_by(OARequest.id.desc())
    )
    if user.role != "admin":
        if user.position_id is None:
            return []
        q = q.where(WorkflowNode.position_id == user.position_id)
    items = db.scalars(q).all()
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


@router.post("/{request_id}/decide", response_model=RequestOut)
def decide(
    request_id: int,
    body: ApprovalDecision,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RequestOut:
    r = db.get(OARequest, request_id)
    if r is None:
        raise HTTPException(status_code=404, detail="申请不存在")
    if r.status != "pending":
        raise HTTPException(status_code=400, detail="该申请已处理")
    if r.current_node_id is None:
        raise HTTPException(status_code=400, detail="该申请未进入审批节点")

    node = db.get(WorkflowNode, r.current_node_id)
    if node is None:
        raise HTTPException(status_code=400, detail="审批流节点异常")
    if user.role != "admin":
        if user.position_id is None or user.position_id != node.position_id:
            raise HTTPException(status_code=403, detail="无权限")

    db.add(
        Approval(
            request_id=r.id,
            workflow_node_id=node.id,
            approver_user_id=user.id,
            decision=body.decision,
            comment=body.comment,
        )
    )

    if body.decision == "rejected":
        r.status = "rejected"
        r.current_node_id = None
        r.approver_user_id = None
        db.add(r)
        db.commit()
        db.refresh(r)
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

    next_node = db.scalar(
        select(WorkflowNode)
        .where(WorkflowNode.workflow_id == node.workflow_id)
        .where(WorkflowNode.step_order > node.step_order)
        .order_by(WorkflowNode.step_order.asc())
    )
    if next_node is None:
        r.status = "approved"
        r.current_node_id = None
        r.approver_user_id = None
    else:
        r.status = "pending"
        r.current_node_id = next_node.id
        # For convenience only; actual permission is by position.
        r.approver_user_id = db.scalar(
            select(User.id)
            .where(User.is_active.is_(True))
            .where(User.position_id == next_node.position_id)
            .order_by(User.id.asc())
        )

    db.add(r)
    db.commit()
    db.refresh(r)

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
