from __future__ import annotations

from pathlib import Path

from my_site.workers.celery_app import celery_app
from my_site.database.db import SessionLocal
from my_site.database.models import (
    ResumeSession,
    ResumeFile,
    ResumeTextVersion,
    ResumeImprovementIteration,
    SessionStatus,
    ResumeSourceType,
)
from my_site.integrations.ocr_client import OCRClient
from my_site.integrations.dify_client import DifyClient


def _safe_str(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


@celery_app.task
def process_resume_session(session_id: int):
    db = SessionLocal()
    session: ResumeSession | None = None

    try:
        session = db.query(ResumeSession).filter_by(id=session_id).first()
        if not session:
            return

        session.status = SessionStatus.PROCESSING
        db.commit()

        resume_file = db.query(ResumeFile).filter_by(id=session.resume_file_id).first()
        if not resume_file:
            raise ValueError(f"ResumeFile not found for session_id={session_id}")

        file_path = Path(resume_file.storage_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Resume file not found: {file_path}")

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        # 1. OCR
        ocr_client = OCRClient()
        ocr_result = ocr_client.extract_file(file_bytes, resume_file.original_filename)
        original_text = (ocr_result.get("text") or "").strip()

        if not original_text:
            raise ValueError("OCR returned empty text")

        original_version = ResumeTextVersion(
            session_id=session.id,
            version_no=1,
            source_type=ResumeSourceType.OCR,
            raw_text=original_text,
            structured_json=ocr_result,
        )
        db.add(original_version)
        db.commit()
        db.refresh(original_version)

        # 2. Dify
        dify_client = DifyClient()
        dify_raw_response = dify_client.analyze_resume(original_text)
        dify_result = dify_client.extract_result_json(dify_raw_response)

        improved_text = dify_client.build_improved_text(original_text, dify_result)

        summary = (
            _safe_str(dify_result.get("summary"))
            or _safe_str(dify_result.get("final_message"))
            or "Resume improvement completed"
        )

        improved_version = ResumeTextVersion(
            session_id=session.id,
            version_no=2,
            source_type=ResumeSourceType.IMPROVED,
            raw_text=improved_text,
            structured_json=dify_result,
        )
        db.add(improved_version)
        db.commit()
        db.refresh(improved_version)

        iteration = ResumeImprovementIteration(
            session_id=session.id,
            input_version_id=original_version.id,
            output_version_id=improved_version.id,
            dify_response_json=dify_raw_response,
            summary=summary,
        )
        db.add(iteration)
        db.commit()
        db.refresh(iteration)

        session.current_iteration = 1
        session.status = SessionStatus.COMPLETED
        db.commit()

    except Exception as e:
        db.rollback()

        if session is not None:
            session.status = SessionStatus.FAILED
            db.add(session)
            db.commit()

        raise RuntimeError(
            f"process_resume_session failed for session_id={session_id}: {e}"
        ) from e

    finally:
        db.close()