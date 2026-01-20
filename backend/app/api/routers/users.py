from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, require_roles
from backend.app.core.security import hash_password
from backend.app.db.models import User
from backend.app.schemas.users import UserCreate, UserOut, UserPasswordUpdate, UserUpdate

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))
) -> list[UserOut]:
    users = db.scalars(select(User).order_by(User.id)).all()
    return [
        UserOut(
            id=u.id,
            username=u.username,
            full_name=u.full_name,
            role=u.role,
            is_active=u.is_active,
            department_id=u.department_id,
            position_id=u.position_id,
        )
        for u in users
    ]


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> UserOut:
    existing = db.scalar(select(User).where(User.username == body.username))
    if existing is not None:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        username=body.username,
        full_name=body.full_name,
        role=body.role,
        department_id=body.department_id,
        position_id=body.position_id,
        password_hash=hash_password(body.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        department_id=user.department_id,
        position_id=user.position_id,
    )


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> UserOut:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    patch = body.model_dump(exclude_unset=True)
    if "full_name" in patch:
        user.full_name = patch["full_name"] or ""
    if "role" in patch:
        user.role = patch["role"] or "employee"
    if "department_id" in patch:
        user.department_id = patch["department_id"]
    if "position_id" in patch:
        user.position_id = patch["position_id"]
    if "is_active" in patch:
        user.is_active = bool(patch["is_active"])

    db.add(user)
    db.commit()
    db.refresh(user)

    return UserOut(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        department_id=user.department_id,
        position_id=user.position_id,
    )


@router.put("/{user_id}/password", status_code=204)
def set_password(
    user_id: int,
    body: UserPasswordUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> None:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.password_hash = hash_password(body.password)
    db.add(user)
    db.commit()
