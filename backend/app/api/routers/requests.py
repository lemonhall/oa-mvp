from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.db.models import OARequest, User
from backend.app.schemas.requests import RequestCreate, RequestOut

router = APIRouter(prefix="/api/requests", tags=["requests"])


def _pick_default_approver(db: Session, creator_id: int) -> int | None:
    approver = db.scalar(
        select(User)
        .where(User.is_active.is_(True))
        .where(User.role.in_(["approver", "admin"]))
        .where(User.id != creator_id)
        .order_by(User.id)
    )
    return approver.id if approver else None


@router.post("", response_model=RequestOut, status_code=201)
def create_request(
    body: RequestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RequestOut:
    if body.type == "reimburse" and body.amount is None:
        raise HTTPException(status_code=400, detail="amount is required for reimburse")

    approver_id = _pick_default_approver(db, user.id)
    req = OARequest(
        type=body.type,
        title=body.title,
        content=body.content,
        amount=body.amount,
        status="pending",
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
    if user.role != "admin" and r.created_by_user_id != user.id and r.approver_user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
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
