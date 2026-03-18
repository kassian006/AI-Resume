from datetime import datetime
from typing import List, Optional
from sqlalchemy import Integer, String, DateTime, ForeignKey, Text, Float, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ats_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    company: Mapped[str] = mapped_column(String(100), default="Google")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job_matches: Mapped[List["JobMatch"]] = relationship("JobMatch", back_populates="resume",
                                                         cascade="all, delete-orphan")

    __table_args__ = (Index("ix_resumes_company", "company"),
        Index("ix_resumes_created_at", "created_at"),)

    def __repr__(self) -> str:
        return f"<Resume(id={self.id}, company={self.company}, ats_score={self.ats_score})>"


class JobMatch(Base):
    __tablename__ = "job_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"),
                                           index=True,nullable=False)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str] = mapped_column(String(100), nullable=False)
    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    job_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    resume: Mapped["Resume"] = relationship("Resume", back_populates="job_matches")

    __table_args__ = (
        Index("ix_job_matches_resume_id", "resume_id"),
        Index("ix_job_matches_company", "company"),
        Index("ix_job_matches_score", "match_score"),
    )

    def __repr__(self) -> str:
        return f"<JobMatch(id={self.id}, title={self.job_title}, score={self.match_score})>"