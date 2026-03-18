from __future__ import annotations
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class ImprovementItem(BaseModel):
    issue: str
    suggestion: str
    example: str


class AnalysisResponse(BaseModel):
    ats_score: float
    strengths: List[str]
    improvements: List[ImprovementItem]
    company_advice: str
    parsed_data: Dict[str, Any]
    resume_id: Optional[int] = None


class JobMatchItem(BaseModel):
    job_title: str
    company: str
    match_score: float
    location: Optional[str] = None
    why_match: List[str]


class MatchJobsResponse(BaseModel):
    matches: List[JobMatchItem]
    total: int


class ResumeInfo(BaseModel):
    id: int
    company: str
    ats_score: Optional[float]
    skills: List[str]
    created_at: datetime

    class Config:
        from_attributes = True