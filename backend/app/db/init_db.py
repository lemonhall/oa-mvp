from sqlalchemy import select

from backend.app.core.security import hash_password
from backend.app.db.base import Base
from backend.app.db.models import User
from backend.app.db.session import SessionLocal, engine


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        def ensure_user(*, username: str, full_name: str, role: str, password: str) -> None:
            user = db.scalar(select(User).where(User.username == username))
            if user is not None:
                return
            db.add(
                User(
                    username=username,
                    full_name=full_name,
                    role=role,
                    password_hash=hash_password(password),
                    is_active=True,
                )
            )

        ensure_user(
            username="admin",
            full_name="Administrator",
            role="admin",
            password="admin123",
        )
        ensure_user(
            username="approver",
            full_name="Approver",
            role="approver",
            password="approver123",
        )
        ensure_user(
            username="employee",
            full_name="Employee",
            role="employee",
            password="employee123",
        )
        db.commit()
