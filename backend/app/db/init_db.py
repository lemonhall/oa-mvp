from sqlalchemy import select

from backend.app.core.security import hash_password
from backend.app.db.base import Base
from backend.app.db.models import Position, User, Workflow, WorkflowNode
from backend.app.db.session import SessionLocal, engine


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        def ensure_position(*, name: str, description: str = "") -> Position:
            pos = db.scalar(select(Position).where(Position.name == name))
            if pos is not None:
                return pos
            pos = Position(name=name, description=description)
            db.add(pos)
            db.flush()
            return pos

        employee_pos = ensure_position(name="员工岗", description="默认员工岗位")
        manager_pos = ensure_position(name="主管岗", description="用于请假/报销等审批")
        finance_pos = ensure_position(name="财务岗", description="用于报销审批")
        admin_pos = ensure_position(name="管理员岗", description="系统管理员")

        def ensure_user(
            *,
            username: str,
            full_name: str,
            role: str,
            password: str,
            position_id: int | None,
        ) -> None:
            user = db.scalar(select(User).where(User.username == username))
            if user is not None:
                return
            db.add(
                User(
                    username=username,
                    full_name=full_name,
                    role=role,
                    password_hash=hash_password(password),
                    position_id=position_id,
                    is_active=True,
                )
            )

        ensure_user(
            username="admin",
            full_name="Administrator",
            role="admin",
            password="admin123",
            position_id=admin_pos.id,
        )
        ensure_user(
            username="approver",
            full_name="Approver",
            role="approver",
            password="approver123",
            position_id=manager_pos.id,
        )
        ensure_user(
            username="finance",
            full_name="Finance",
            role="employee",
            password="finance123",
            position_id=finance_pos.id,
        )
        ensure_user(
            username="employee",
            full_name="Employee",
            role="employee",
            password="employee123",
            position_id=employee_pos.id,
        )

        def ensure_workflow(
            *,
            name: str,
            request_type: str,
            is_active: bool,
            nodes: list[tuple[int, int, str]],
        ) -> None:
            wf = db.scalar(select(Workflow).where(Workflow.name == name))
            if wf is not None:
                return
            wf = Workflow(name=name, request_type=request_type, is_active=is_active)
            db.add(wf)
            db.flush()

            for step_order, position_id, node_name in nodes:
                db.add(
                    WorkflowNode(
                        workflow_id=wf.id,
                        step_order=step_order,
                        position_id=position_id,
                        name=node_name,
                    )
                )

        ensure_workflow(
            name="默认请假审批流",
            request_type="leave",
            is_active=True,
            nodes=[(1, manager_pos.id, "主管审批")],
        )
        ensure_workflow(
            name="默认报销审批流",
            request_type="reimburse",
            is_active=True,
            nodes=[(1, manager_pos.id, "主管审批"), (2, finance_pos.id, "财务审批")],
        )

        db.commit()
