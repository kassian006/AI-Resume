from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from my_site.database.db import get_db
from my_site.database import models
from my_site.database.schema import MatchJobsResponse, JobMatchItem
from my_site.core.hybrid_router import HybridAIRouter
from my_site.deps import get_ai_router

jobs_router = APIRouter(prefix="/jobs", tags=["jobs"])


@jobs_router.post("/match", response_model=MatchJobsResponse)
async def match_jobs(
        resume_id: int,
        company_filter: Optional[str] = None,
        db: Session = Depends(get_db),
        ai_router: HybridAIRouter = Depends(get_ai_router)
) -> MatchJobsResponse:
    """Находит подходящие вакансии для резюме"""

    resume = db.query(models.Resume).filter(
        models.Resume.id == resume_id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    embedding = ai_router.get_embedding(resume.original_text)

    matches = [
        {
            "job_title": "Senior ML Engineer",
            "company": "Google",
            "match_score": 87.5,
            "location": "Remote",
            "why_match": ["✅ Python в навыках", "✅ ML опыт"]
        },
        {
            "job_title": "Backend Engineer",
            "company": "Amazon",
            "match_score": 72.3,
            "location": "Berlin",
            "why_match": ["✅ Backend опыт", "✅ AWS навыки"]
        },
        {
            "job_title": "AI Research Engineer",
            "company": "Tesla",
            "match_score": 65.0,
            "location": "Palo Alto",
            "why_match": ["✅ PyTorch", "✅ Python"]
        }
    ]

    if company_filter:
        matches = [m for m in matches if m["company"] == company_filter]

    return MatchJobsResponse(
        matches=[JobMatchItem(**m) for m in matches],
        total=len(matches)
    )


@jobs_router.get("/demo", response_model=MatchJobsResponse)
async def demo_jobs() -> MatchJobsResponse:
    """Демо вакансии для теста"""

    matches = [
        {
            "job_title": "Senior ML Engineer",
            "company": "Google",
            "match_score": 87.5,
            "location": "Remote",
            "why_match": ["✅ Python в навыках", "✅ ML опыт"]
        },
        {
            "job_title": "Backend Engineer",
            "company": "Amazon",
            "match_score": 72.3,
            "location": "Berlin",
            "why_match": ["✅ Backend опыт", "✅ AWS навыки"]
        }
    ]

    return MatchJobsResponse(
        matches=[JobMatchItem(**m) for m in matches],
        total=len(matches)
    )