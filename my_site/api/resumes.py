from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from my_site.database.db import get_db
from my_site.database.models import (
    User,
    ResumeFile,
    ResumeSession,
    ResumeImprovementIteration,
    SessionType,
    SessionStatus,
)
from my_site.database.schema import (
    ResumeUploadQueuedResponse,
    ResumeSessionDetailResponse,
    ResumeSessionListItemResponse,
    # ResumeTextVersionResponse,
    ResumeAnalysisResultResponse,
    ResumeImprovementErrorItem,
)
from my_site.core.security import get_current_user
from my_site.workers.tasks import process_resume_session

resumes_router = APIRouter(prefix="/resumes", tags=["resumes"])

MEDIA_ROOT = Path("media")
RESUMES_DIR = MEDIA_ROOT / "resumes"


def _parse_result_from_iteration(iteration: ResumeImprovementIteration | None,) -> ResumeAnalysisResultResponse:
    if not iteration:
        return ResumeAnalysisResultResponse()

    payload = iteration.dify_response_json
    if not isinstance(payload, dict):
        return ResumeAnalysisResultResponse()

    greeting = payload.get("greeting", "")
    final_message = payload.get("final_message", "")
    raw_errors = payload.get("errors", [])

    errors: list[ResumeImprovementErrorItem] = []

    if isinstance(raw_errors, list):
        for item in raw_errors:
            if not isinstance(item, dict):
                continue

            original = item.get("original", "")
            improved = item.get("improved", "")
            advice = item.get("advice", "")

            if (isinstance(original, str)
                and isinstance(improved, str)
                and isinstance(advice, str)):
                errors.append(
                    ResumeImprovementErrorItem(
                        original=original,
                        improved=improved,
                        advice=advice,
                    ))

    return ResumeAnalysisResultResponse(
        greeting=greeting if isinstance(greeting, str) else "",
        errors=errors,
        final_message=final_message if isinstance(final_message, str) else "",
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
        status=session.status.value if hasattr(session.status, "value") else str(session.status),
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

    iterations = sorted(session.improvement_iterations or [], key=lambda x: x.id)
    latest_iteration = iterations[-1] if iterations else None
    result = _parse_result_from_iteration(latest_iteration)

    return ResumeSessionDetailResponse(
        session_id=session.id,
        resume_file_id=session.resume_file_id,
        filename=session.resume_file.original_filename if session.resume_file else "",
        status=session.status,
        current_iteration=session.current_iteration,
        result=result,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


# @resumes_router.get(
#     "/sessions/{session_id}/versions",
#     response_model=list[ResumeTextVersionResponse],
# )
# def get_versions(
#     session_id: int,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     session = (
#         db.query(ResumeSession)
#         .filter(
#             ResumeSession.id == session_id,
#             ResumeSession.user_id == current_user.id,
#         )
#         .first()
#     )
#
#     if not session:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Session not found",
#         )
#
#     return []