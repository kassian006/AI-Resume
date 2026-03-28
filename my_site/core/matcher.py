from __future__ import annotations
from typing import Any


SKILLS_DB = [
    "python", "fastapi", "django", "flask",
    "sql", "sqlalchemy", "postgresql", "mysql", "mongodb", "redis",
    "docker", "kubernetes", "linux", "git", "bash",
    "javascript", "typescript", "react", "vue", "node",
    "java", "spring", "c#", ".net", "golang", "go",
    "pandas", "numpy", "pytorch", "tensorflow",
    "machine learning", "ml", "data analysis", "data analyst",
    "backend", "frontend", "fullstack", "devops",
    "aws", "gcp", "azure", "ci/cd",
    "ios", "android", "swift", "kotlin",
    "ocr", "opencv", "pytesseract", "pdf", "rest api",
]


class ResumeJobMatcher:
    def normalize_text(self, text: str) -> str:
        return " ".join((text or "").lower().split())

    def extract_skills(self, resume_text: str) -> list[str]:
        text = self.normalize_text(resume_text)
        found: list[str] = []

        for skill in SKILLS_DB:
            if skill in text and skill not in found:
                found.append(skill)

        return found

    def match(
        self,
        jobs: list[dict[str, Any]],
        resume_text: str,
    ) -> tuple[list[str], list[dict[str, Any]]]:
        skills = self.extract_skills(resume_text)

        if not skills:
            return [], []

        matched: list[dict[str, Any]] = []

        for job in jobs:
            job_title = self.normalize_text(job.get("job_title", ""))
            job_text = " ".join([
                job_title,
                self.normalize_text(job.get("company", "")),
                self.normalize_text(job.get("location", "")),
                self.normalize_text(job.get("salary", "")),
            ])

            matched_skills: list[str] = []
            score = 0

            for skill in skills:
                if skill in job_title:
                    matched_skills.append(skill)
                    score += 3
                elif skill in job_text:
                    matched_skills.append(skill)
                    score += 1

            if score >= 2:
                job_copy = job.copy()
                job_copy["match_score"] = score
                job_copy["why_match"] = matched_skills
                matched.append(job_copy)

        matched.sort(key=lambda j: j["match_score"], reverse=True)
        return skills, matched[:20]