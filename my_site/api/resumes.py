from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from my_site.database.db import get_db
from my_site.database.models import (
    User,
    ResumeFile,
    ResumeSession,
    ResumeTextVersion,
    ResumeImprovementIteration,
    SessionType,
    SessionStatus,
    ResumeSourceType,
)
from my_site.database.schema import (
    ResumeUploadQueuedResponse,
    ResumeSessionDetailResponse,
    ResumeSessionListItemResponse,
    ResumeTextVersionResponse,
    ResumeVersionBriefResponse,
    ResumeSessionResultResponse,
    ResumeImprovementErrorItem,
)
from my_site.core.security import get_current_user
from my_site.workers.tasks import process_resume_session

resumes_router = APIRouter(prefix="/resumes", tags=["resumes"])

MEDIA_ROOT = Path("media")
RESUMES_DIR = MEDIA_ROOT / "resumes"


def _extract_errors_from_iteration(
    iteration: ResumeImprovementIteration | None,
) -> list[ResumeImprovementErrorItem]:
    if not iteration:
        return []

    payload = iteration.dify_response_json
    if not isinstance(payload, dict):
        return []

    # ожидаем либо сырой Dify response, либо уже нормализованный json
    result_obj: dict[str, Any] | None = None

    data = payload.get("data")
    if isinstance(data, dict):
        outputs = data.get("outputs")
        if isinstance(outputs, dict):
            maybe_result = outputs.get("result")
            if isinstance(maybe_result, dict):
                result_obj = maybe_result

    if result_obj is None:
        result_obj = payload

    raw_errors = result_obj.get("errors")
    if not isinstance(raw_errors, list):
        return []

    parsed_errors: list[ResumeImprovementErrorItem] = []

    for item in raw_errors:
        if not isinstance(item, dict):
            continue

        original = item.get("original")
        improved = item.get("improved")
        advice = item.get("advice")

        if (
            isinstance(original, str)
            and isinstance(improved, str)
            and isinstance(advice, str)
        ):
            parsed_errors.append(
                ResumeImprovementErrorItem(
                    original=original,
                    improved=improved,
                    advice=advice,
                )
            )

    return parsed_errors


def _extract_summary(
    iteration: ResumeImprovementIteration | None,
    improved_version: ResumeTextVersion | None,
) -> str | None:
    if iteration and isinstance(iteration.summary, str) and iteration.summary.strip():
        return iteration.summary.strip()

    if improved_version and isinstance(improved_version.structured_json, dict):
        structured = improved_version.structured_json

        for key in ("summary", "final_message"):
            value = structured.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return None


def _to_version_brief(version: ResumeTextVersion | None) -> ResumeVersionBriefResponse | None:
    if version is None:
        return None

    return ResumeVersionBriefResponse(
        id=version.id,
        version_no=version.version_no,
        source_type=version.source_type,
        raw_text=version.raw_text,
        structured_json=version.structured_json,
        created_at=version.created_at,
    )


def _build_session_detail(session: ResumeSession) -> ResumeSessionDetailResponse:
    versions = sorted(session.text_versions or [], key=lambda x: x.version_no)
    iterations = sorted(session.improvement_iterations or [], key=lambda x: x.id)

    original_version = next(
        (v for v in versions if v.source_type in {ResumeSourceType.OCR, ResumeSourceType.PDF_TEXT}),
        None,
    )

    improved_version = next(
        (v for v in reversed(versions) if v.source_type == ResumeSourceType.IMPROVED),
        None,
    )

    latest_iteration = iterations[-1] if iterations else None

    errors = _extract_errors_from_iteration(latest_iteration)
    summary = _extract_summary(latest_iteration, improved_version)

    return ResumeSessionDetailResponse(
        session_id=session.id,
        resume_file_id=session.resume_file_id,
        filename=session.resume_file.original_filename if session.resume_file else "",
        status=session.status,
        current_iteration=session.current_iteration,
        original_version=_to_version_brief(original_version),
        improved_version=_to_version_brief(improved_version),
        result=ResumeSessionResultResponse(
            errors=errors,
            summary=summary,
        ),
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@resumes_router.post(
    "/upload",
    response_model=ResumeUploadQueuedResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing",
        )

    ext = Path(file.filename).suffix.lower()
    if ext != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )

    file_bytes = file.file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    RESUMES_DIR.mkdir(parents=True, exist_ok=True)

    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    storage_path = RESUMES_DIR / unique_name

    with open(storage_path, "wb") as f:
        f.write(file_bytes)

    resume_file = ResumeFile(
        user_id=current_user.id,
        original_filename=file.filename,
        storage_path=str(storage_path).replace("\\", "/"),
        mime_type=file.content_type or "application/pdf",
        file_size=len(file_bytes),
    )
    db.add(resume_file)
    db.commit()
    db.refresh(resume_file)

    session = ResumeSession(
        user_id=current_user.id,
        resume_file_id=resume_file.id,
        session_type=SessionType.IMPROVE,
        status=SessionStatus.QUEUED,
        current_iteration=0,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    process_resume_session.delay(session.id)

    return ResumeUploadQueuedResponse(
        resume_file_id=resume_file.id,
        session_id=session.id,
        filename=resume_file.original_filename,
        status=session.status.value,
        message="Resume uploaded and queued for processing",
    )


@resumes_router.get(
    "/sessions",
    response_model=list[ResumeSessionListItemResponse],
)
def list_resume_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sessions = (
        db.query(ResumeSession)
        .options(joinedload(ResumeSession.resume_file))
        .filter(ResumeSession.user_id == current_user.id)
        .order_by(ResumeSession.created_at.desc())
        .all()
    )

    return [
        ResumeSessionListItemResponse(
            session_id=session.id,
            resume_file_id=session.resume_file_id,
            filename=session.resume_file.original_filename if session.resume_file else "",
            status=session.status,
            current_iteration=session.current_iteration,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
        for session in sessions
    ]


@resumes_router.get(
    "/sessions/{session_id}",
    response_model=ResumeSessionDetailResponse,
)
def get_resume_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = (
        db.query(ResumeSession)
        .options(
            joinedload(ResumeSession.resume_file),
            joinedload(ResumeSession.text_versions),
            joinedload(ResumeSession.improvement_iterations),
        )
        .filter(
            ResumeSession.id == session_id,
            ResumeSession.user_id == current_user.id,
        )
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    return _build_session_detail(session)


@resumes_router.get(
    "/sessions/{session_id}/versions",
    response_model=list[ResumeTextVersionResponse],
)
def get_versions(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = (
        db.query(ResumeSession)
        .filter(
            ResumeSession.id == session_id,
            ResumeSession.user_id == current_user.id,
        )
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    versions = (
        db.query(ResumeTextVersion)
        .filter(ResumeTextVersion.session_id == session_id)
        .order_by(ResumeTextVersion.version_no.asc())
        .all()
    )

    return versions