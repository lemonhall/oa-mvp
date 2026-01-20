import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.db.models import (
    Approval,
    OARequest,
    Position,
    ProcessType,
    User,
    Workflow,
    WorkflowNode,
)
from backend.app.schemas.requests import (
    ApprovalHistoryItem,
    RequestCreate,
    RequestDetail,
    RequestNodeStatus,
    RequestOut,
)

router = APIRouter(prefix="/api/requests", tags=["requests"])


def _get_active_workflow(db: Session, request_type: str) -> Workflow | None:
    items = db.scalars(
        select(Workflow)
        .where(Workflow.request_type == request_type)
        .where(Workflow.is_active.is_(True))
        .order_by(Workflow.id.asc())
    ).all()
    if len(items) > 1:
        raise HTTPException(status_code=400, detail="同一类型只能启用一个审批流")
    return items[0] if items else None


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


def _request_out(req: OARequest) -> RequestOut:
    # Keep list responses lean; form data is returned in /detail.
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


def _can_view_request(db: Session, *, req: OARequest, user: User) -> bool:
    if user.role == "admin":
        return True
    if req.created_by_user_id == user.id:
        return True
    if req.status != "pending" or req.current_node_id is None or user.position_id is None:
        return False
    node = db.get(WorkflowNode, req.current_node_id)
    return node is not None and node.position_id == user.position_id


@router.post("", response_model=RequestOut, status_code=201)
def create_request(
    body: RequestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RequestOut:
    process = db.scalar(
        select(ProcessType).where(ProcessType.code == body.type).where(ProcessType.is_active.is_(True))
    )
    if process is None:
        raise HTTPException(status_code=400, detail="申请类型不存在或已停用")

    if process.requires_amount and body.amount is None:
        raise HTTPException(status_code=400, detail="该申请类型需要填写金额")

    try:
        fields = json.loads(process.schema_json or "[]")
    except Exception:
        fields = []

    if fields and isinstance(body.data, dict):
        for f in fields:
            if not isinstance(f, dict):
                continue
            if not f.get("required"):
                continue
            key = f.get("key")
            if not key:
                continue
            v = body.data.get(key)
            if v is None:
                raise HTTPException(status_code=400, detail=f"请填写：{f.get('label') or key}")
            if isinstance(v, str) and not v.strip():
                raise HTTPException(status_code=400, detail=f"请填写：{f.get('label') or key}")

    wf = _get_active_workflow(db, body.type)
    if wf is None:
        raise HTTPException(status_code=400, detail="该类型暂无启用的审批流")
    first_node = _get_first_node(db, wf.id)
    if first_node is None:
        raise HTTPException(status_code=400, detail="审批流未配置节点")

    approver_id = _pick_assignee_by_position(
        db, position_id=first_node.position_id, exclude_user_id=user.id
    )
    req = OARequest(
        type=body.type,
        title=body.title,
        content=body.content,
        amount=body.amount,
        data_json=json.dumps(body.data or {}, ensure_ascii=False),
        status="pending",
        workflow_id=wf.id,
        current_node_id=first_node.id,
        created_by_user_id=user.id,
        approver_user_id=approver_id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return _request_out(req)


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
        _request_out(r)
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
        raise HTTPException(status_code=404, detail="申请不存在")
    if not _can_view_request(db, req=r, user=user):
        raise HTTPException(status_code=403, detail="无权限")
    return _request_out(r)


@router.get("/{request_id}/detail", response_model=RequestDetail)
def get_request_detail(
    request_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RequestDetail:
    r = db.get(OARequest, request_id)
    if r is None:
        raise HTTPException(status_code=404, detail="申请不存在")
    if not _can_view_request(db, req=r, user=user):
        raise HTTPException(status_code=403, detail="无权限")

    process_name = None
    form_data: dict = {}
    p = db.scalar(select(ProcessType).where(ProcessType.code == r.type))
    if p is not None:
        process_name = p.name
    try:
        form_data = json.loads(r.data_json or "{}")
        if not isinstance(form_data, dict):
            form_data = {}
    except Exception:
        form_data = {}

    wf_name = None
    nodes: list[RequestNodeStatus] = []
    if r.workflow_id is not None:
        wf = db.get(Workflow, r.workflow_id)
        wf_name = wf.name if wf else None

        node_rows = db.execute(
            select(WorkflowNode, Position)
            .join(Position, WorkflowNode.position_id == Position.id)
            .where(WorkflowNode.workflow_id == r.workflow_id)
            .order_by(WorkflowNode.step_order.asc())
        ).all()

        approvals = db.execute(
            select(Approval, User, WorkflowNode, Position)
            .join(User, Approval.approver_user_id == User.id)
            .outerjoin(WorkflowNode, Approval.workflow_node_id == WorkflowNode.id)
            .outerjoin(Position, WorkflowNode.position_id == Position.id)
            .where(Approval.request_id == r.id)
            .order_by(Approval.id.asc())
        ).all()

        approved_by_node: dict[int, tuple[Approval, User]] = {}
        for a, u, n, _p in approvals:
            if n is None:
                continue
            approved_by_node[n.id] = (a, u)

        for n, p in node_rows:
            a_u = approved_by_node.get(n.id)
            if a_u:
                a, au = a_u
                node_status = a.decision  # approved / rejected
                nodes.append(
                    RequestNodeStatus(
                        node_id=n.id,
                        step_order=n.step_order,
                        node_name=n.name,
                        position_id=p.id,
                        position_name=p.name,
                        status=node_status,
                        decided_by_user_id=au.id,
                        decided_by_username=au.username,
                        decided_at=a.decided_at,
                        comment=a.comment,
                    )
                )
                continue

            if r.status == "pending" and r.current_node_id == n.id:
                nodes.append(
                    RequestNodeStatus(
                        node_id=n.id,
                        step_order=n.step_order,
                        node_name=n.name,
                        position_id=p.id,
                        position_name=p.name,
                        status="pending",
                    )
                )
            else:
                nodes.append(
                    RequestNodeStatus(
                        node_id=n.id,
                        step_order=n.step_order,
                        node_name=n.name,
                        position_id=p.id,
                        position_name=p.name,
                        status="not_started",
                    )
                )

        history = [
            ApprovalHistoryItem(
                id=a.id,
                workflow_node_id=(n.id if n else None),
                step_order=(n.step_order if n else None),
                node_name=(n.name if n else None),
                position_id=(p.id if p else None),
                position_name=(p.name if p else None),
                approver_user_id=u.id,
                approver_username=u.username,
                decision=a.decision,
                comment=a.comment,
                decided_at=a.decided_at,
            )
            for a, u, n, p in approvals
        ]
    else:
        history = []

    return RequestDetail(
        request=_request_out(r),
        process_name=process_name,
        form_data=form_data,
        workflow_name=wf_name,
        nodes=nodes,
        history=history,
    )
