from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db, require_roles
from backend.app.db.models import Announcement, User
from backend.app.schemas.announcements import AnnouncementCreate, AnnouncementOut

router = APIRouter(prefix="/api/announcements", tags=["announcements"])


@router.get("", response_model=list[AnnouncementOut])
def list_announcements(
    db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> list[AnnouncementOut]:
    items = db.scalars(select(Announcement).order_by(Announcement.id.desc())).all()
    return [
        AnnouncementOut(
            id=a.id,
            title=a.title,
            content=a.content,
            created_by_user_id=a.created_by_user_id,
            created_at=a.created_at,
        )
        for a in items
    ]


@router.post("", response_model=AnnouncementOut, status_code=201)
def create_announcement(
    body: AnnouncementCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
) -> AnnouncementOut:
    a = Announcement(title=body.title, content=body.content, created_by_user_id=user.id)
    db.add(a)
    db.commit()
    db.refresh(a)
    return AnnouncementOut(
        id=a.id,
        title=a.title,
        content=a.content,
        created_by_user_id=a.created_by_user_id,
        created_at=a.created_at,
    )
