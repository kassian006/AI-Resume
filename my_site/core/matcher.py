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
    def extract_skills(self, resume_text: str) -> list[str]:
        text = resume_text.lower()
        found: list[str] = []

        for skill in SKILLS_DB:
            if skill in text and skill not in found:
                found.append(skill)

        return found

    def match(
        self,
        jobs: list[dict[str, Any]],
        resume_text: str,
    ) -> list[dict[str, Any]]:
        skills = self.extract_skills(resume_text)

        if not skills:
            return jobs

        matched: list[dict[str, Any]] = []

        for job in jobs:
            job_title = (job.get("job_title") or "").lower()
            job_text = " ".join([
                job_title,
                (job.get("company") or "").lower(),
                (job.get("location") or "").lower(),
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

            if score > 0:
                job_copy = job.copy()
                job_copy["match_score"] = score
                job_copy["why_match"] = matched_skills
                matched.append(job_copy)

        matched.sort(key=lambda j: j["match_score"], reverse=True)
        return matched