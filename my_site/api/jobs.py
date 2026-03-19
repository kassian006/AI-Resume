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
async def match_jobs(resume_id: int,location: str = "KG",db: Session = Depends(get_db),
                     ai_router: HybridAIRouter = Depends(get_ai_router)) -> MatchJobsResponse:

    resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(404, "Resume not found")

    # ✅ Простая логика: разные источники для разных локаций
    if location.upper() == "KG":
        matches = _get_kg_jobs(resume, ai_router)
    else:
        matches = _get_international_jobs(resume, ai_router)

    return MatchJobsResponse(matches=matches, total=len(matches))


def _get_kg_jobs(resume: models.Resume, ai_router) -> List[dict]:
    """Вакансии для Кыргызстана/СНГ (моковые данные + логика)"""
    # В реальном проекте: парсинг dev.kg, hh.kg, Telegram API
    base_jobs = [
        {
            "job_title": "Python Backend Developer",
            "company": "NambaPay",
            "location": "Bishkek, KG",
            "match_score": 92.0,
            "source": "dev.kg",
            "why_match": ["✅ Python", "✅ FastAPI", "✅ Локальный рынок"],
            "salary": "800-1500 USD",
            "remote": False
        },
        {
            "job_title": "ML Engineer",
            "company": "Beeline KG",
            "location": "Bishkek, KG",
            "match_score": 85.0,
            "source": "hh.kg",
            "why_match": ["✅ PyTorch", "✅ SQL", "✅ Телеком опыт"],
            "salary": "1000-2000 USD",
            "remote": True
        },
        {
            "job_title": "Data Analyst",
            "company": "Optima Bank",
            "location": "Bishkek, KG",
            "match_score": 78.0,
            "source": "Telegram: Dev KG Jobs",
            "why_match": ["✅ Pandas", "✅ Визуализация"],
            "salary": "600-1200 USD",
            "remote": False
        }
    ]
    return _filter_by_skills(base_jobs, resume)


def _get_international_jobs(resume: models.Resume, ai_router) -> List[dict]:
    """Вакансии для зарубежья (моковые данные)"""
    base_jobs = [
        {
            "job_title": "Senior ML Engineer",
            "company": "Google",
            "location": "Berlin, DE",
            "match_score": 88.0,
            "source": "LinkedIn",
            "why_match": ["✅ PyTorch", "✅ Big Tech experience", "✅ English C1"],
            "salary": "€70k-90k",
            "remote": True,
            "visa_support": True
        },
        {
            "job_title": "AI Research Scientist",
            "company": "Meta",
            "location": "London, UK",
            "match_score": 82.0,
            "source": "Meta Careers",
            "why_match": ["✅ Publications", "✅ TensorFlow", "✅ Research"],
            "salary": "£80k-110k",
            "remote": False,
            "visa_support": True
        }
    ]
    return _filter_by_skills(base_jobs, resume)


def _filter_by_skills(jobs: List[dict], resume: models.Resume) -> List[dict]:
    """Простая фильтрация по навыкам из резюме"""
    if not resume.parsed_data:
        return jobs

    resume_skills = set(s.lower() for s in resume.parsed_data.get("skills", []))

    filtered = []
    for job in jobs:
        # Упрощённая логика: если есть хотя бы 2 совпадения — показываем
        job_keywords = job.get("job_title", "").lower() + " " + job.get("company", "").lower()
        matches = sum(1 for skill in resume_skills if skill in job_keywords)

        if matches >= 1:  # Порог можно настроить
            filtered.append(job)

    return sorted(filtered, key=lambda x: x["match_score"], reverse=True)


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