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
    ResumeAnalysisResultResponse,
    ResumeImprovementErrorItem,
    ResumeMatchResultResponse,
)
from my_site.core.security import get_current_user
from my_site.workers.tasks import process_resume_session, process_match_session

resumes_router = APIRouter(prefix="/resumes", tags=["resumes"])

MEDIA_ROOT = Path("media")
RESUMES_DIR = MEDIA_ROOT / "resumes"


def _save_uploaded_pdf(
    *,
    file: UploadFile,
    db: Session,
    current_user: User,
) -> ResumeFile:
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

    return resume_file


def _create_session(
    *,
    db: Session,
    current_user: User,
    resume_file: ResumeFile,
    session_type: SessionType,
) -> ResumeSession:
    session = ResumeSession(
        user_id=current_user.id,
        resume_file_id=resume_file.id,
        session_type=session_type,
        status=SessionStatus.QUEUED,
        current_iteration=0,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _parse_result_from_iteration(
    iteration: ResumeImprovementIteration | None,
) -> ResumeAnalysisResultResponse:
    if not iteration:
        return ResumeAnalysisResultResponse()

    payload = iteration.dify_response_json
    if not isinstance(payload, dict):
        return ResumeAnalysisResultResponse()

    greeting = payload.get("greeting", "")
    status_value = payload.get("status", "")
    improved_resume = payload.get("improved_resume", "")
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

            if (
                isinstance(original, str)
                and isinstance(improved, str)
                and isinstance(advice, str)
            ):
                errors.append(
                    ResumeImprovementErrorItem(
                        original=original,
                        improved=improved,
                        advice=advice,
                    )
                )

    return ResumeAnalysisResultResponse(
        greeting=greeting if isinstance(greeting, str) else "",
        status=status_value if isinstance(status_value, str) else "",
        improved_resume=improved_resume if isinstance(improved_resume, str) else "",
        errors=errors,
        final_message=final_message if isinstance(final_message, str) else "",
    )


def _parse_match_result_from_iteration(
    iteration: ResumeImprovementIteration | None,
) -> tuple[list[str], list[dict], str]:
    if not iteration:
        return [], [], ""

    payload = iteration.dify_response_json
    if not isinstance(payload, dict):
        return [], [], ""

    skills_found = payload.get("skills_found", [])
    jobs = payload.get("jobs", [])
    final_message = payload.get("final_message", "")

    if not isinstance(skills_found, list):
        skills_found = []

    if not isinstance(jobs, list):
        jobs = []

    if not isinstance(final_message, str):
        final_message = ""

    normalized_jobs = []
    for job in jobs:
        if isinstance(job, dict):
            normalized_jobs.append(job)

    normalized_skills = [s for s in skills_found if isinstance(s, str)]

    return normalized_skills, normalized_jobs, final_message


@resumes_router.post(
    "/upload",
    response_model=ResumeUploadQueuedResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_resume_for_analysis(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume_file = _save_uploaded_pdf(
        file=file,
        db=db,
        current_user=current_user,
    )

    session = _create_session(
        db=db,
        current_user=current_user,
        resume_file=resume_file,
        session_type=SessionType.IMPROVE,
    )

    process_resume_session.delay(session.id)

    return ResumeUploadQueuedResponse(
        resume_file_id=resume_file.id,
        session_id=session.id,
        filename=resume_file.original_filename,
        status=session.status.value if hasattr(session.status, "value") else str(session.status),
        message="Resume uploaded and queued for analysis",
    )


@resumes_router.post(
    "/match-upload",
    response_model=ResumeUploadQueuedResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_resume_for_matching(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume_file = _save_uploaded_pdf(
        file=file,
        db=db,
        current_user=current_user,
    )

    session = _create_session(
        db=db,
        current_user=current_user,
        resume_file=resume_file,
        session_type=SessionType.MATCH,
    )

    process_match_session.delay(session.id)

    return ResumeUploadQueuedResponse(
        resume_file_id=resume_file.id,
        session_id=session.id,
        filename=resume_file.original_filename,
        status=session.status.value if hasattr(session.status, "value") else str(session.status),
        message="Resume uploaded and queued for job matching",
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
            session_type=session.session_type,
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
        session_type=session.session_type,
        status=session.status,
        current_iteration=session.current_iteration,
        result=result,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )

@resumes_router.get(
    "/sessions/{session_id}/matches",
    response_model=ResumeMatchResultResponse,
)
def get_resume_session_matches(
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

    if session.session_type != SessionType.MATCH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This session is not a job matching session",
        )

    iterations = sorted(session.improvement_iterations or [], key=lambda x: x.id)
    latest_iteration = iterations[-1] if iterations else None

    skills_found, jobs, final_message = _parse_match_result_from_iteration(latest_iteration)

    return ResumeMatchResultResponse(
        session_id=session.id,
        resume_file_id=session.resume_file_id,
        filename=session.resume_file.original_filename if session.resume_file else "",
        status=session.status,
        current_iteration=session.current_iteration,
        skills_found=skills_found,
        jobs=jobs,
        final_message=final_message,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )
