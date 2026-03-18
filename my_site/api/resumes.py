from __future__ import annotations
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from my_site.database.db import get_db
from my_site.database import models
from my_site.database.schema import AnalysisResponse, ResumeInfo
from my_site.core.parser import ResumeParser
from my_site.core.hybrid_router import HybridAIRouter
from my_site.deps import get_resume_parser, get_ai_router

resumes_router = APIRouter(prefix="/resumes", tags=["resumes"])


@resumes_router.post("/analyze", response_model=AnalysisResponse)
async def analyze_resume(
        file: UploadFile = File(..., description="PDF резюме"),
        company: str = "Google",
        db: Session = Depends(get_db),
        parser: ResumeParser = Depends(get_resume_parser),
        ai_router: HybridAIRouter = Depends(get_ai_router)
) -> AnalysisResponse:
    """Анализирует резюме и дает советы"""

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        file_bytes = await file.read()

        parsed_data = parser.parse(file_bytes)

        analysis = ai_router.analyze_resume(
            resume_text=parsed_data["raw_text"],
            company=company
        )

        resume = models.Resume(
            original_text=parsed_data["raw_text"],
            parsed_data=parsed_data,
            ats_score=analysis.get("ats_score", 0),
            company=company
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        return AnalysisResponse(
            ats_score=analysis.get("ats_score", 0),
            strengths=analysis.get("strengths", []),
            improvements=analysis.get("improvements", []),
            company_advice=analysis.get("company_specific_advice", ""),
            parsed_data=parsed_data,
            resume_id=resume.id
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@resumes_router.get("/", response_model=List[ResumeInfo])
async def list_resumes(
        limit: int = 10,
        db: Session = Depends(get_db)
) -> List[ResumeInfo]:
    """Список всех резюме"""

    resumes = db.query(models.Resume).order_by(
        models.Resume.created_at.desc()
    ).limit(limit).all()

    return [
        ResumeInfo(
            id=r.id,
            company=r.company,
            ats_score=r.ats_score,
            skills=r.parsed_data.get("skills", []) if r.parsed_data else [],
            created_at=r.created_at
        )
        for r in resumes
    ]


@resumes_router.get("/{resume_id}", response_model=ResumeInfo)
async def get_resume(
        resume_id: int,
        db: Session = Depends(get_db)
) -> ResumeInfo:
    """Получить информацию о резюме по ID"""

    resume = db.query(models.Resume).filter(
        models.Resume.id == resume_id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    skills = resume.parsed_data.get("skills", []) if resume.parsed_data else []

    return ResumeInfo(
        id=resume.id,
        company=resume.company,
        ats_score=resume.ats_score,
        skills=skills,
        created_at=resume.created_at
    )

@resumes_router.post("/fix-bullet")
async def fix_bullet(
    original: str,
    company: str = "Google",
    ai_router: HybridAIRouter = Depends(get_ai_router)
):
    return {"fixed": ai_router.fix_resume_bullet(original, company)}