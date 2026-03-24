from datetime import datetime
from typing import Optional, Any, List
from enum import Enum as PyEnum
from sqlalchemy import DateTime,Enum,Float,ForeignKey,Index,Integer,String,Text,UniqueConstraint,Boolean,func,JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base


class SessionType(str, PyEnum):
    IMPROVE = "improve"
    MATCH = "match"

class SessionStatus(str, PyEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class ResumeSourceType(str, PyEnum):
    PDF_TEXT = "pdf_text"
    OCR = "ocr"
    IMPROVED = "improved"


class JobSourceType(str, PyEnum):
    API = "api"
    SCRAPER = "scraper"
    MANUAL = "manual"
    TELEGRAM = "telegram"
    OTHER = "other"


class ApiProvider(str, PyEnum):
    OCR = "ocr"
    DIFY = "dify"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    external_auth_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    resume_files: Mapped[list["ResumeFile"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    resume_sessions: Mapped[list["ResumeSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    refresh_token: Mapped[List['RefreshToken']] = relationship(back_populates='users',
                                                               cascade='all, delete-orphan')


class RefreshToken(Base):
    __tablename__ = 'refresh_token'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    users: Mapped[User] = relationship(back_populates='refresh_token')
    token: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __str__(self):
        return self.token



class ResumeFile(Base):
    __tablename__ = "resume_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="resume_files")

    sessions: Mapped[list["ResumeSession"]] = relationship(
        back_populates="resume_file",
        cascade="all, delete-orphan",
    )


class ResumeSession(Base):
    __tablename__ = "resume_sessions"
    __table_args__ = (
        Index("ix_resume_sessions_user_status", "user_id", "status"),
        Index("ix_resume_sessions_user_type", "user_id", "session_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    resume_file_id: Mapped[int] = mapped_column(
        ForeignKey("resume_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    session_type: Mapped[SessionType] = mapped_column(
        Enum(SessionType, name="session_type_enum", native_enum=True),
        nullable=False,
        index=True,
    )

    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status_enum", native_enum=True),
        nullable=False,
        default=SessionStatus.QUEUED,
        server_default=SessionStatus.QUEUED.name,
        index=True,
    )

    current_iteration: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="resume_sessions")
    resume_file: Mapped["ResumeFile"] = relationship(back_populates="sessions")

    text_versions: Mapped[list["ResumeTextVersion"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ResumeTextVersion.version_no",
    )

    improvement_iterations: Mapped[list["ResumeImprovementIteration"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ResumeImprovementIteration.id",
    )

    job_matches: Mapped[list["JobMatch"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class ResumeTextVersion(Base):
    __tablename__ = "resume_text_versions"
    __table_args__ = (
        UniqueConstraint("session_id", "version_no", name="uq_resume_text_versions_session_version"),
        Index("ix_resume_text_versions_session_source", "session_id", "source_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    session_id: Mapped[int] = mapped_column(
        ForeignKey("resume_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    version_no: Mapped[int] = mapped_column(Integer, nullable=False)

    source_type: Mapped[ResumeSourceType] = mapped_column(
        Enum(ResumeSourceType, name="resume_source_type_enum", native_enum=True),
        nullable=False,
        index=True,
    )

    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    structured_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    session: Mapped["ResumeSession"] = relationship(back_populates="text_versions")

    input_iterations: Mapped[list["ResumeImprovementIteration"]] = relationship(
        back_populates="input_version",
        foreign_keys="ResumeImprovementIteration.input_version_id",
    )

    output_iterations: Mapped[list["ResumeImprovementIteration"]] = relationship(
        back_populates="output_version",
        foreign_keys="ResumeImprovementIteration.output_version_id",
    )

    job_matches: Mapped[list["JobMatch"]] = relationship(
        back_populates="resume_version",
        cascade="all, delete-orphan",
    )


class ResumeImprovementIteration(Base):
    __tablename__ = "resume_improvement_iterations"
    __table_args__ = (
        Index("ix_resume_improvement_iterations_session", "session_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    session_id: Mapped[int] = mapped_column(
        ForeignKey("resume_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    input_version_id: Mapped[int] = mapped_column(
        ForeignKey("resume_text_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    output_version_id: Mapped[int] = mapped_column(
        ForeignKey("resume_text_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    dify_response_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    ats_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    session: Mapped["ResumeSession"] = relationship(back_populates="improvement_iterations")

    input_version: Mapped["ResumeTextVersion"] = relationship(
        back_populates="input_iterations",
        foreign_keys=[input_version_id],
    )

    output_version: Mapped["ResumeTextVersion"] = relationship(
        back_populates="output_iterations",
        foreign_keys=[output_version_id],
    )


class JobSource(Base):
    __tablename__ = "job_sources"
    __table_args__ = (
        UniqueConstraint("name", name="uq_job_sources_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[JobSourceType] = mapped_column(
        Enum(JobSourceType, name="job_source_type_enum", native_enum=True),
        nullable=False,
        index=True,
    )
    base_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    jobs: Mapped[list["Job"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
    )


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_jobs_source_external"),
        Index("ix_jobs_title", "title"),
        Index("ix_jobs_company", "company"),
        Index("ix_jobs_is_active", "is_active"),
        Index("ix_jobs_published_at", "published_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    source_id: Mapped[int] = mapped_column(
        ForeignKey("job_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    external_id: Mapped[str] = mapped_column(String(255), nullable=False)

    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    company: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    salary: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    employment_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    skills_json: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    source: Mapped["JobSource"] = relationship(back_populates="jobs")

    matches: Mapped[list["JobMatch"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )


class JobMatch(Base):
    __tablename__ = "job_matches"
    __table_args__ = (
        Index("ix_job_matches_session_score", "session_id", "match_score"),
        UniqueConstraint(
            "session_id",
            "resume_version_id",
            "job_id",
            name="uq_job_matches_session_version_job",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    session_id: Mapped[int] = mapped_column(
        ForeignKey("resume_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    resume_version_id: Mapped[int] = mapped_column(
        ForeignKey("resume_text_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    match_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)

    why_match_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    gap_skills_json: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    session: Mapped["ResumeSession"] = relationship(back_populates="job_matches")
    resume_version: Mapped["ResumeTextVersion"] = relationship(back_populates="job_matches")
    job: Mapped["Job"] = relationship(back_populates="matches")


class ApiLog(Base):
    __tablename__ = "api_logs"
    __table_args__ = (
        Index("ix_api_logs_provider_created_at", "provider", "created_at"),
        Index("ix_api_logs_request_id", "request_id"),
        Index("ix_api_logs_status_code", "status_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    provider: Mapped[ApiProvider] = mapped_column(
        Enum(ApiProvider, name="api_provider_enum", native_enum=True),
        nullable=False,
        index=True,
    )

    request_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )