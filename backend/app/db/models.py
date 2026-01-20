from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


def utcnow() -> datetime:
    return datetime.utcnow()


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    users: Mapped[list["User"]] = relationship(back_populates="department")


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(255), default="")

    users: Mapped[list["User"]] = relationship(back_populates="position")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="employee", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    department_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("departments.id"), nullable=True
    )
    department: Mapped[Department | None] = relationship(back_populates="users")

    position_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("positions.id"), nullable=True
    )
    position: Mapped[Position | None] = relationship(back_populates="users")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    content: Mapped[str] = mapped_column(Text, default="")
    created_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    created_by: Mapped[User] = relationship()


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    request_type: Mapped[str] = mapped_column(String(30), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    nodes: Mapped[list["WorkflowNode"]] = relationship(
        back_populates="workflow", cascade="all, delete-orphan"
    )


class WorkflowNode(Base):
    __tablename__ = "workflow_nodes"
    __table_args__ = (UniqueConstraint("workflow_id", "step_order"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_id: Mapped[int] = mapped_column(Integer, ForeignKey("workflows.id"))
    step_order: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(200), default="")
    position_id: Mapped[int] = mapped_column(Integer, ForeignKey("positions.id"))

    workflow: Mapped[Workflow] = relationship(back_populates="nodes")
    position: Mapped[Position] = relationship()


class OARequest(Base):
    __tablename__ = "oa_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String(30), index=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    content: Mapped[str] = mapped_column(Text, default="")
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)

    workflow_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("workflows.id"), nullable=True
    )
    current_node_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("workflow_nodes.id"), nullable=True
    )

    created_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    approver_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    created_by: Mapped[User] = relationship(foreign_keys=[created_by_user_id])
    approver: Mapped[User | None] = relationship(foreign_keys=[approver_user_id])
    workflow: Mapped[Workflow | None] = relationship()
    current_node: Mapped[WorkflowNode | None] = relationship(foreign_keys=[current_node_id])

    approvals: Mapped[list["Approval"]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(Integer, ForeignKey("oa_requests.id"))
    workflow_node_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("workflow_nodes.id"), nullable=True
    )
    approver_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(20))
    comment: Mapped[str] = mapped_column(Text, default="")
    decided_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    request: Mapped[OARequest] = relationship(back_populates="approvals")
    approver: Mapped[User] = relationship()
    workflow_node: Mapped[WorkflowNode | None] = relationship()
