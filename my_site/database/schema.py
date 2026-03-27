from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, EmailStr, ConfigDict, Field

from .models import (
    SessionType,
    SessionStatus,
    ResumeSourceType,
    JobSourceType,
    ApiProvider,
)


# =========================
# Base
# =========================

class ORMBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# =========================
# Auth / User
# =========================

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class UserResponse(ORMBaseSchema):
    id: int
    email: EmailStr
    external_auth_id: Optional[str] = None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# =========================
# Resume File
# =========================

class ResumeFileCreate(BaseModel):
    original_filename: str
    storage_path: str
    mime_type: str
    file_size: int


class ResumeFileResponse(ORMBaseSchema):
    id: int
    user_id: int
    original_filename: str
    storage_path: str
    mime_type: str
    file_size: int
    uploaded_at: datetime


# =========================
# Resume Session
# =========================

class ResumeSessionCreate(BaseModel):
    resume_file_id: int
    session_type: SessionType


class ResumeSessionUpdate(BaseModel):
    status: Optional[SessionStatus] = None
    current_iteration: Optional[int] = None


class ResumeSessionResponse(ORMBaseSchema):
    id: int
    user_id: int
    resume_file_id: int
    session_type: SessionType
    status: SessionStatus
    current_iteration: int
    created_at: datetime
    updated_at: datetime


class ResumeSessionStopRequest(BaseModel):
    stop: bool = True


class ResumeSessionContinueRequest(BaseModel):
    target_company: Optional[str] = None
    notes: Optional[str] = None


# =========================
# Resume Text Version
# =========================

class ResumeTextVersionCreate(BaseModel):
    session_id: int
    version_no: int
    source_type: ResumeSourceType
    raw_text: str
    structured_json: Optional[dict[str, Any]] = None


class ResumeTextVersionUpdate(BaseModel):
    raw_text: Optional[str] = None
    structured_json: Optional[dict[str, Any]] = None


class ResumeTextVersionResponse(ORMBaseSchema):
    id: int
    session_id: int
    version_no: int
    source_type: ResumeSourceType
    raw_text: str
    structured_json: Optional[dict[str, Any]] = None
    created_at: datetime


# =========================
# Resume Improvement Iteration
# =========================

class ResumeImprovementIterationCreate(BaseModel):
    session_id: int
    input_version_id: int
    output_version_id: Optional[int] = None
    dify_response_json: Optional[dict[str, Any]] = None
    ats_score: Optional[float] = None
    summary: Optional[str] = None


class ResumeImprovementIterationResponse(ORMBaseSchema):
    id: int
    session_id: int
    input_version_id: int
    output_version_id: Optional[int] = None
    dify_response_json: Optional[dict[str, Any]] = None
    ats_score: Optional[float] = None
    summary: Optional[str] = None
    created_at: datetime

    input_version: Optional["ResumeTextVersionResponse"] = None
    output_version: Optional["ResumeTextVersionResponse"] = None


# =========================
# Job Source
# =========================

class JobSourceCreate(BaseModel):
    name: str
    source_type: JobSourceType
    base_url: Optional[str] = None


class JobSourceResponse(ORMBaseSchema):
    id: int
    name: str
    source_type: JobSourceType
    base_url: Optional[str] = None


# =========================
# Job
# =========================

class JobCreate(BaseModel):
    source_id: int
    external_id: str
    title: str
    company: str
    description: str
    location: Optional[str] = None
    salary: Optional[str] = None
    employment_type: Optional[str] = None
    skills_json: Optional[list[Any]] = None
    is_active: bool = True
    published_at: Optional[datetime] = None


class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    employment_type: Optional[str] = None
    skills_json: Optional[list[Any]] = None
    is_active: Optional[bool] = None
    published_at: Optional[datetime] = None


class JobResponse(ORMBaseSchema):
    id: int
    source_id: int
    external_id: str
    title: str
    company: str
    description: str
    location: Optional[str] = None
    salary: Optional[str] = None
    employment_type: Optional[str] = None
    skills_json: Optional[list[Any]] = None
    is_active: bool
    published_at: Optional[datetime] = None

    source: Optional["JobSourceResponse"] = None


# =========================
# Job Match
# =========================

class JobMatchCreate(BaseModel):
    session_id: int
    resume_version_id: int
    job_id: int
    match_score: float
    why_match_json: Optional[dict[str, Any]] = None
    gap_skills_json: Optional[list[Any]] = None


class JobMatchResponse(ORMBaseSchema):
    id: int
    session_id: int
    resume_version_id: int
    job_id: int
    match_score: float
    why_match_json: Optional[dict[str, Any]] = None
    gap_skills_json: Optional[list[Any]] = None
    created_at: datetime

    job: Optional["JobResponse"] = None
    resume_version: Optional["ResumeTextVersionResponse"] = None


# =========================
# API Log
# =========================

class ApiLogCreate(BaseModel):
    provider: ApiProvider
    request_id: Optional[str] = None
    status_code: Optional[int] = None
    latency_ms: Optional[int] = None
    error_text: Optional[str] = None


class ApiLogResponse(ORMBaseSchema):
    id: int
    provider: ApiProvider
    request_id: Optional[str] = None
    status_code: Optional[int] = None
    latency_ms: Optional[int] = None
    error_text: Optional[str] = None
    created_at: datetime


# =========================
# Resume workflow payloads
# =========================

class ResumeImproveStartResponse(BaseModel):
    session: ResumeSessionResponse
    version: ResumeTextVersionResponse
    iteration: Optional[ResumeImprovementIterationResponse] = None


class ResumeImproveContinueRequest(BaseModel):
    resume_text: str
    target_company: Optional[str] = None
    iteration_history: list[dict[str, Any]] = Field(default_factory=list)
    conversation_id: Optional[str] = None


class ResumeImproveResultResponse(BaseModel):
    source_type: ResumeSourceType
    structured: dict[str, Any]
    dify_result: dict[str, Any]


# =========================
# Job matching payloads
# =========================

class JobMatchRunRequest(BaseModel):
    resume_session_id: int
    resume_version_id: int
    limit: int = Field(default=20, ge=1, le=100)


class JobMatchRunResponse(BaseModel):
    session_id: int
    resume_version_id: int
    total_matches: int
    matches: list[JobMatchResponse]


# =========================
# Generic responses
# =========================

class MessageResponse(BaseModel):
    message: str


class PaginatedResponse(BaseModel):
    total: int
    items: list[Any]


# =========================
# Resume upload responses
# =========================

class ResumeUploadResponse(BaseModel):
    resume_file_id: int
    session_id: int
    version_id: int
    filename: str
    extracted_chars: int
    message: str


class ResumeUploadQueuedResponse(BaseModel):
    resume_file_id: int
    session_id: int
    filename: str
    status: str
    message: str


# =========================
# Resume analysis result
# =========================

class ResumeImprovementErrorItem(BaseModel):
    original: str
    improved: str
    advice: str


class ResumeAnalysisResultResponse(BaseModel):
    greeting: str = ""
    errors: list[ResumeImprovementErrorItem] = Field(default_factory=list)
    final_message: str = ""


class ResumeSessionDetailResponse(BaseModel):
    session_id: int
    resume_file_id: int
    filename: str
    status: SessionStatus
    current_iteration: int
    result: ResumeAnalysisResultResponse = Field(default_factory=ResumeAnalysisResultResponse)
    created_at: datetime
    updated_at: datetime


class ResumeSessionListItemResponse(BaseModel):
    session_id: int
    resume_file_id: int
    filename: str
    status: SessionStatus
    current_iteration: int
    created_at: datetime
    updated_at: datetime


ResumeImprovementIterationResponse.model_rebuild()
JobResponse.model_rebuild()
JobMatchResponse.model_rebuild()