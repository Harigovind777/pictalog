"""Endpoints the image helper on the Mac calls. Authenticated with the shared worker token, not a user login."""

import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from pictalog.api.deps import read_upload
from pictalog.auth import current_user
from pictalog.db import get_db
from pictalog.jobs import claim_next, complete_extract, complete_image, fail_job, heartbeat, helper_status
from pictalog.models import Import, Job, User
from pictalog.schemas import ExtractedItem

router = APIRouter(prefix="/api")


def worker_auth(request: Request) -> None:
    token = request.headers.get("x-worker-token", "")
    if not secrets.compare_digest(token.encode(), request.app.state.settings.worker_token.encode()):
        raise HTTPException(401, "Wrong worker token.")


class ClaimIn(BaseModel):
    engine: str | None = None


class JobOut(BaseModel):
    id: int
    kind: str
    payload: dict


class ItemsIn(BaseModel):
    items: list[ExtractedItem]


class FailIn(BaseModel):
    error: str


class HelperStatus(BaseModel):
    online: bool
    last_seen_at: datetime | None
    engine: str | None


def _job(db: Session, job_id: int) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(404, "Job not found.")
    return job


@router.post("/worker/claim", dependencies=[Depends(worker_auth)], response_model=JobOut | None)
def claim(body: ClaimIn, db: Session = Depends(get_db)):
    job = claim_next(db, body.engine)
    if job is None:
        return Response(status_code=204)
    return JobOut(id=job.id, kind=job.kind, payload=job.payload)


@router.post("/worker/heartbeat", dependencies=[Depends(worker_auth)], status_code=204)
def worker_heartbeat(body: ClaimIn, db: Session = Depends(get_db)) -> Response:
    heartbeat(db, body.engine)
    return Response(status_code=204)


@router.get("/worker/jobs/{job_id}/file", dependencies=[Depends(worker_auth)])
def job_file(job_id: int, request: Request, db: Session = Depends(get_db)) -> Response:
    job = _job(db, job_id)
    imp = db.get(Import, job.import_id) if job.kind == "extract" and job.import_id else None
    if imp is None:
        raise HTTPException(404, "This job has no file.")
    return Response(request.app.state.storage.read(imp.file_key), media_type="application/octet-stream")


@router.post("/worker/jobs/{job_id}/image", dependencies=[Depends(worker_auth)], status_code=204)
async def job_image(job_id: int, file: UploadFile, request: Request, db: Session = Depends(get_db)) -> Response:
    job = _job(db, job_id)
    try:
        complete_image(db, request.app.state.storage, job, await read_upload(file, request))
    except ValueError:
        fail_job(db, job, "The helper sent something that isn't an image.")
        raise HTTPException(400, "Not an image.") from None
    return Response(status_code=204)


@router.post("/worker/jobs/{job_id}/items", dependencies=[Depends(worker_auth)], status_code=204)
def job_items(job_id: int, body: ItemsIn, db: Session = Depends(get_db)) -> Response:
    complete_extract(db, _job(db, job_id), body.items)
    return Response(status_code=204)


@router.post("/worker/jobs/{job_id}/fail", dependencies=[Depends(worker_auth)], status_code=204)
def job_fail(job_id: int, body: FailIn, db: Session = Depends(get_db)) -> Response:
    fail_job(db, _job(db, job_id), body.error)
    return Response(status_code=204)


@router.get("/helper/status")
def get_helper_status(user: User = Depends(current_user), db: Session = Depends(get_db)) -> HelperStatus:
    return HelperStatus(**helper_status(db))
