from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api.routers import (
    announcements,
    approvals,
    auth,
    depts,
    positions,
    requests,
    users,
    workflows,
)
from backend.app.core.config import settings
from backend.app.db.init_db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="OA MVP", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(depts.router)
app.include_router(positions.router)
app.include_router(workflows.router)
app.include_router(announcements.router)
app.include_router(requests.router)
app.include_router(approvals.router)


@app.get("/api/health")
def health():
    return {"ok": True}


root_dir = Path(__file__).resolve().parents[2]
frontend_dir = root_dir / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
