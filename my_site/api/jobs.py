from fastapi import APIRouter, HTTPException, UploadFile, File

from my_site.core.job_aggregator import JobAggregator
from my_site.core.matcher import ResumeJobMatcher
from my_site.core.parser import extract_text_from_pdf_bytes
from my_site.database.schema import MatchResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])

aggregator = JobAggregator()
matcher = ResumeJobMatcher()


@router.get("/health")
def jobs_health():
    return {"status": "ok"}


@router.post("/match-from-file", response_model=MatchResponse)
async def match_jobs_from_file(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_bytes = await file.read()
    resume_text = extract_text_from_pdf_bytes(file_bytes)

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from resume")

    jobs = aggregator.collect_all_jobs()
    skills_found, matched_jobs = matcher.match(jobs, resume_text)

    return MatchResponse(
        total=len(matched_jobs),
        skills_found=skills_found,
        jobs=matched_jobs,
    )