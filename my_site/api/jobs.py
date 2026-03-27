from fastapi import APIRouter, HTTPException

from my_site.core.job_aggregator import JobAggregator
from my_site.core.matcher import ResumeJobMatcher
from my_site.database.schema import MatchRequest, MatchResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])

aggregator = JobAggregator()
matcher = ResumeJobMatcher()


@router.get("/health")
def jobs_health():
    return {"status": "ok"}


@router.post("/match", response_model=MatchResponse)
def match_jobs(payload: MatchRequest):
    resume_text = payload.resume_text.strip()

    if not resume_text:
        raise HTTPException(status_code=400, detail="resume_text is empty")

    jobs = aggregator.collect_all_jobs()
    matched_jobs = matcher.match(jobs, resume_text)

    return MatchResponse(
        total=len(matched_jobs),
        jobs=matched_jobs,
    )