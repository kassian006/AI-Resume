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


@celery_app.task(name="my_site.workers.tasks.process_resume_session")
def process_resume_session(session_id: int):
    db = SessionLocal()
    session: ResumeSession | None = None

    try:
        session = db.query(ResumeSession).filter_by(id=session_id).first()
        if not session:
            return

        # Отдельно фиксируем PROCESSING, чтобы фронт сразу видел изменение статуса
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

        # 1. OCR only
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
        db.flush()  # нужен id без промежуточного commit

        # 2. Dify analysis
        dify_client = DifyClient()
        dify_raw_response = dify_client.analyze_resume(original_text)
        dify_result = dify_client.extract_result_json(dify_raw_response)
        import json
        print("DIFY RESULT:", json.dumps(dify_result, indent=2, ensure_ascii=False))

        summary = (
            _safe_str(dify_result.get("final_message"))
            or _safe_str(dify_result.get("summary"))
            or "Resume analysis completed"
        )

        iteration = ResumeImprovementIteration(
            session_id=session.id,
            input_version_id=original_version.id,
            output_version_id=None,
            dify_response_json=dify_result,
            summary=summary,
        )
        db.add(iteration)

        session.current_iteration = 1
        session.status = SessionStatus.COMPLETED

        # Один финальный commit на все результаты
        db.commit()

    except Exception as e:
        db.rollback()

        if session is not None:
            try:
                session.status = SessionStatus.FAILED
                db.add(session)
                db.commit()
            except Exception:
                db.rollback()

        raise RuntimeError(
            f"process_resume_session failed for session_id={session_id}: {e}"
        ) from e

    finally:
        db.close()