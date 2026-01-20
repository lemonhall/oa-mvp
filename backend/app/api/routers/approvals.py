from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, require_roles
from backend.app.db.models import Approval, OARequest, User
from backend.app.schemas.requests import ApprovalDecision, RequestOut

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


@router.get("/pending", response_model=list[RequestOut])
def list_pending(
    db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "approver"))
) -> list[RequestOut]:
    q = (
        select(OARequest)
        .where(OARequest.status == "pending")
        .where(OARequest.approver_user_id == user.id)
        .order_by(OARequest.id.desc())
    )
    items = db.scalars(q).all()
    return [
        RequestOut(
            id=r.id,
            type=r.type,
            title=r.title,
            content=r.content,
            amount=r.amount,
            status=r.status,
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
    user: User = Depends(require_roles("admin", "approver")),
) -> RequestOut:
    r = db.get(OARequest, request_id)
    if r is None:
        raise HTTPException(status_code=404, detail="Request not found")
    if r.status != "pending":
        raise HTTPException(status_code=400, detail="Request already decided")
    if user.role != "admin" and r.approver_user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    r.status = body.decision
    if r.approver_user_id is None:
        r.approver_user_id = user.id

    db.add(
        Approval(
            request_id=r.id,
            approver_user_id=user.id,
            decision=body.decision,
            comment=body.comment,
        )
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
        created_by_user_id=r.created_by_user_id,
        approver_user_id=r.approver_user_id,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )
