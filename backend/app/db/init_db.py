import json

from sqlalchemy import select

from backend.app.core.security import hash_password
from backend.app.db.base import Base
from backend.app.db.models import Position, ProcessType, User, Workflow, WorkflowNode
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
        hr_pos = ensure_position(name="人事岗", description="用于人事相关审批/备案")
        ceo_pos = ensure_position(name="总经理岗", description="用于最终审批")
        legal_pos = ensure_position(name="法务岗", description="用于合同/用章等审批")
        procurement_pos = ensure_position(name="采购岗", description="用于采购审批")
        admin_affairs_pos = ensure_position(name="行政岗", description="用于用章/资产等审批")
        it_pos = ensure_position(name="IT岗", description="用于权限/账号等审批")
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
            username="hr",
            full_name="HR",
            role="employee",
            password="hr123456",
            position_id=hr_pos.id,
        )
        ensure_user(
            username="ceo",
            full_name="CEO",
            role="employee",
            password="ceo123456",
            position_id=ceo_pos.id,
        )
        ensure_user(
            username="employee",
            full_name="Employee",
            role="employee",
            password="employee123",
            position_id=employee_pos.id,
        )
        ensure_user(
            username="legal",
            full_name="Legal",
            role="employee",
            password="legal123456",
            position_id=legal_pos.id,
        )
        ensure_user(
            username="procurement",
            full_name="Procurement",
            role="employee",
            password="procurement123456",
            position_id=procurement_pos.id,
        )
        ensure_user(
            username="admin_affairs",
            full_name="Admin Affairs",
            role="employee",
            password="adminaffairs123456",
            position_id=admin_affairs_pos.id,
        )
        ensure_user(
            username="it",
            full_name="IT",
            role="employee",
            password="it123456",
            position_id=it_pos.id,
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

        def ensure_process_type(
            *,
            code: str,
            name: str,
            description: str,
            requires_amount: bool,
            fields: list[dict],
            is_active: bool = True,
        ) -> None:
            p = db.scalar(select(ProcessType).where(ProcessType.code == code))
            if p is not None:
                return
            db.add(
                ProcessType(
                    code=code,
                    name=name,
                    description=description,
                    requires_amount=requires_amount,
                    is_active=is_active,
                    schema_json=json.dumps(fields, ensure_ascii=False),
                )
            )

        ensure_process_type(
            code="leave",
            name="请假",
            description="请假申请/审批",
            requires_amount=False,
            fields=[
                {"key": "leave_type", "label": "请假类型", "type": "select", "required": True, "options": ["事假", "病假", "年假", "调休", "其他"]},
                {"key": "start_date", "label": "开始日期", "type": "date", "required": True},
                {"key": "end_date", "label": "结束日期", "type": "date", "required": True},
                {"key": "days", "label": "天数", "type": "number", "required": False},
            ],
        )
        ensure_process_type(
            code="reimburse",
            name="报销",
            description="费用报销",
            requires_amount=True,
            fields=[
                {"key": "category", "label": "报销类别", "type": "select", "required": True, "options": ["差旅", "招待", "办公", "项目", "其他"]},
                {"key": "invoice", "label": "发票信息", "type": "text", "required": False},
            ],
        )
        ensure_process_type(
            code="travel",
            name="出差",
            description="出差申请",
            requires_amount=False,
            fields=[
                {"key": "destination", "label": "目的地", "type": "text", "required": True},
                {"key": "start_date", "label": "开始日期", "type": "date", "required": True},
                {"key": "end_date", "label": "结束日期", "type": "date", "required": True},
                {"key": "plan", "label": "行程/事项", "type": "textarea", "required": False},
            ],
        )
        ensure_process_type(
            code="overtime",
            name="加班",
            description="加班申请",
            requires_amount=False,
            fields=[
                {"key": "date", "label": "加班日期", "type": "date", "required": True},
                {"key": "hours", "label": "小时数", "type": "number", "required": True},
                {"key": "reason", "label": "加班原因", "type": "textarea", "required": True},
            ],
        )
        ensure_process_type(
            code="purchase",
            name="采购",
            description="采购申请",
            requires_amount=True,
            fields=[
                {"key": "items", "label": "采购清单", "type": "textarea", "required": True},
                {"key": "vendor", "label": "供应商（可选）", "type": "text", "required": False},
            ],
        )
        ensure_process_type(
            code="payment",
            name="付款",
            description="付款申请",
            requires_amount=True,
            fields=[
                {"key": "payee", "label": "收款方", "type": "text", "required": True},
                {"key": "bank", "label": "开户行/账号", "type": "text", "required": True},
                {"key": "reason", "label": "付款事由", "type": "textarea", "required": True},
            ],
        )
        ensure_process_type(
            code="seal",
            name="用章",
            description="用章申请",
            requires_amount=False,
            fields=[
                {"key": "seal_type", "label": "印章类型", "type": "select", "required": True, "options": ["公章", "合同章", "财务章", "其他"]},
                {"key": "usage", "label": "用途说明", "type": "textarea", "required": True},
            ],
        )
        ensure_process_type(
            code="contract",
            name="合同",
            description="合同审批/归档",
            requires_amount=False,
            fields=[
                {"key": "counterparty", "label": "对方单位", "type": "text", "required": True},
                {"key": "subject", "label": "合同标的", "type": "text", "required": True},
                {"key": "summary", "label": "合同要点", "type": "textarea", "required": False},
            ],
        )
        ensure_process_type(
            code="budget",
            name="预算",
            description="预算申请/调整",
            requires_amount=True,
            fields=[
                {"key": "period", "label": "预算周期", "type": "text", "required": True},
                {"key": "reason", "label": "调整原因", "type": "textarea", "required": False},
            ],
        )
        ensure_process_type(
            code="loan",
            name="借款",
            description="借款/备用金",
            requires_amount=True,
            fields=[
                {"key": "reason", "label": "借款用途", "type": "textarea", "required": True},
                {"key": "repay_date", "label": "预计归还日期", "type": "date", "required": False},
            ],
        )
        ensure_process_type(
            code="hiring",
            name="招聘",
            description="招聘/编制申请",
            requires_amount=False,
            fields=[
                {"key": "position", "label": "岗位名称", "type": "text", "required": True},
                {"key": "headcount", "label": "人数", "type": "number", "required": True},
                {"key": "reason", "label": "招聘原因", "type": "textarea", "required": True},
            ],
        )
        ensure_process_type(
            code="hr_change",
            name="人事异动",
            description="入职/转正/调岗/离职等",
            requires_amount=False,
            fields=[
                {"key": "change_type", "label": "异动类型", "type": "select", "required": True, "options": ["入职", "转正", "调岗", "离职"]},
                {"key": "employee_name", "label": "员工姓名", "type": "text", "required": True},
                {"key": "effective_date", "label": "生效日期", "type": "date", "required": True},
            ],
        )
        ensure_process_type(
            code="asset",
            name="资产",
            description="资产领用/归还",
            requires_amount=False,
            fields=[
                {"key": "asset_name", "label": "资产名称", "type": "text", "required": True},
                {"key": "asset_sn", "label": "资产编号/序列号", "type": "text", "required": False},
                {"key": "action", "label": "动作", "type": "select", "required": True, "options": ["领用", "归还"]},
            ],
        )
        ensure_process_type(
            code="project",
            name="项目",
            description="项目立项/变更/结项",
            requires_amount=False,
            fields=[
                {"key": "project_name", "label": "项目名称", "type": "text", "required": True},
                {"key": "action", "label": "动作", "type": "select", "required": True, "options": ["立项", "变更", "结项"]},
                {"key": "summary", "label": "说明", "type": "textarea", "required": False},
            ],
        )
        ensure_process_type(
            code="invoice",
            name="开票",
            description="发票开具申请",
            requires_amount=True,
            fields=[
                {"key": "buyer", "label": "购方名称", "type": "text", "required": True},
                {"key": "tax_no", "label": "税号", "type": "text", "required": True},
                {"key": "content", "label": "开票内容", "type": "text", "required": True},
            ],
        )
        ensure_process_type(
            code="access",
            name="权限开通",
            description="系统账号/权限申请",
            requires_amount=False,
            fields=[
                {"key": "system", "label": "系统名称", "type": "text", "required": True},
                {"key": "account", "label": "账号/邮箱", "type": "text", "required": True},
                {"key": "permissions", "label": "权限说明", "type": "textarea", "required": True},
            ],
        )

        ensure_workflow(
            name="默认请假审批流",
            request_type="leave",
            is_active=True,
            nodes=[(1, manager_pos.id, "主管审批")],
        )
        ensure_workflow(
            name="请假-主管-总经理",
            request_type="leave",
            is_active=False,
            nodes=[(1, manager_pos.id, "主管审批"), (2, ceo_pos.id, "总经理审批")],
        )
        ensure_workflow(
            name="请假-主管-人事备案",
            request_type="leave",
            is_active=False,
            nodes=[(1, manager_pos.id, "主管审批"), (2, hr_pos.id, "人事备案")],
        )
        ensure_workflow(
            name="默认报销审批流",
            request_type="reimburse",
            is_active=True,
            nodes=[(1, manager_pos.id, "主管审批"), (2, finance_pos.id, "财务审批")],
        )
        ensure_workflow(
            name="报销-主管-财务-总经理",
            request_type="reimburse",
            is_active=False,
            nodes=[
                (1, manager_pos.id, "主管审批"),
                (2, finance_pos.id, "财务审批"),
                (3, ceo_pos.id, "总经理审批"),
            ],
        )

        ensure_workflow(
            name="出差-主管-总经理",
            request_type="travel",
            is_active=True,
            nodes=[(1, manager_pos.id, "主管审批"), (2, ceo_pos.id, "总经理审批")],
        )
        ensure_workflow(
            name="加班-主管-人事",
            request_type="overtime",
            is_active=True,
            nodes=[(1, manager_pos.id, "主管审批"), (2, hr_pos.id, "人事备案")],
        )
        ensure_workflow(
            name="采购-主管-采购-财务-总经理",
            request_type="purchase",
            is_active=True,
            nodes=[
                (1, manager_pos.id, "主管审批"),
                (2, procurement_pos.id, "采购审批"),
                (3, finance_pos.id, "财务审批"),
                (4, ceo_pos.id, "总经理审批"),
            ],
        )
        ensure_workflow(
            name="付款-主管-财务-总经理",
            request_type="payment",
            is_active=True,
            nodes=[
                (1, manager_pos.id, "主管审批"),
                (2, finance_pos.id, "财务审批"),
                (3, ceo_pos.id, "总经理审批"),
            ],
        )
        ensure_workflow(
            name="用章-主管-法务-行政-总经理",
            request_type="seal",
            is_active=True,
            nodes=[
                (1, manager_pos.id, "主管审批"),
                (2, legal_pos.id, "法务审核"),
                (3, admin_affairs_pos.id, "行政用章"),
                (4, ceo_pos.id, "总经理审批"),
            ],
        )
        ensure_workflow(
            name="合同-法务-财务-总经理",
            request_type="contract",
            is_active=True,
            nodes=[
                (1, legal_pos.id, "法务审核"),
                (2, finance_pos.id, "财务审核"),
                (3, ceo_pos.id, "总经理审批"),
            ],
        )
        ensure_workflow(
            name="预算-主管-财务-总经理",
            request_type="budget",
            is_active=True,
            nodes=[
                (1, manager_pos.id, "主管审批"),
                (2, finance_pos.id, "财务审批"),
                (3, ceo_pos.id, "总经理审批"),
            ],
        )
        ensure_workflow(
            name="借款-主管-财务-总经理",
            request_type="loan",
            is_active=True,
            nodes=[
                (1, manager_pos.id, "主管审批"),
                (2, finance_pos.id, "财务审批"),
                (3, ceo_pos.id, "总经理审批"),
            ],
        )
        ensure_workflow(
            name="招聘-主管-人事-总经理",
            request_type="hiring",
            is_active=True,
            nodes=[
                (1, manager_pos.id, "主管审批"),
                (2, hr_pos.id, "人事审核"),
                (3, ceo_pos.id, "总经理审批"),
            ],
        )
        ensure_workflow(
            name="人事异动-人事-主管-总经理",
            request_type="hr_change",
            is_active=True,
            nodes=[
                (1, hr_pos.id, "人事审核"),
                (2, manager_pos.id, "主管确认"),
                (3, ceo_pos.id, "总经理审批"),
            ],
        )
        ensure_workflow(
            name="资产-主管-行政-IT",
            request_type="asset",
            is_active=True,
            nodes=[
                (1, manager_pos.id, "主管审批"),
                (2, admin_affairs_pos.id, "行政处理"),
                (3, it_pos.id, "IT处理"),
            ],
        )
        ensure_workflow(
            name="项目-主管-总经理",
            request_type="project",
            is_active=True,
            nodes=[(1, manager_pos.id, "主管审批"), (2, ceo_pos.id, "总经理审批")],
        )
        ensure_workflow(
            name="开票-财务-总经理",
            request_type="invoice",
            is_active=True,
            nodes=[(1, finance_pos.id, "财务审核"), (2, ceo_pos.id, "总经理审批")],
        )
        ensure_workflow(
            name="权限开通-主管-IT",
            request_type="access",
            is_active=True,
            nodes=[(1, manager_pos.id, "主管审批"), (2, it_pos.id, "IT开通")],
        )

        db.commit()
