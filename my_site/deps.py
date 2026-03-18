from __future__ import annotations
from typing import Generator
from sqlalchemy.orm import Session
from my_site.database.db import get_db
from my_site.database.db import SessionLocal
from my_site.core.parser import ResumeParser
from my_site.core.hybrid_router import HybridAIRouter
from my_site.config import GEMINI_API_KEY


def get_resume_parser() -> ResumeParser:
    return ResumeParser()


def get_ai_router() -> HybridAIRouter:
    return HybridAIRouter(gemini_api_key=GEMINI_API_KEY)