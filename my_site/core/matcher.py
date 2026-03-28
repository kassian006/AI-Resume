from __future__ import annotations

from typing import Any


SKILL_ALIASES: dict[str, list[str]] = {
    "python": ["python"],
    "fastapi": ["fastapi"],
    "django": ["django"],
    "flask": ["flask"],
    "sql": ["sql"],
    "sqlalchemy": ["sqlalchemy"],
    "postgresql": ["postgresql", "postgres", "psql"],
    "mysql": ["mysql"],
    "mongodb": ["mongodb", "mongo"],
    "redis": ["redis"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes", "k8s"],
    "linux": ["linux"],
    "git": ["git", "github", "gitlab"],
    "bash": ["bash", "shell"],
    "javascript": ["javascript", "js"],
    "typescript": ["typescript", "ts"],
    "react": ["react", "react.js", "reactjs"],
    "vue": ["vue", "vue.js", "vuejs"],
    "node": ["node", "nodejs", "node.js"],
    "java": ["java"],
    "spring": ["spring", "spring boot"],
    "c#": ["c#", ".net", "dotnet", "asp.net"],
    "golang": ["golang", "go"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "pytorch": ["pytorch"],
    "tensorflow": ["tensorflow"],
    "machine learning": ["machine learning", "ml"],
    "data analysis": ["data analysis", "data analyst", "analytics"],
    "backend": ["backend", "back-end", "server-side"],
    "frontend": ["frontend", "front-end", "ui"],
    "fullstack": ["fullstack", "full-stack"],
    "devops": ["devops"],
    "aws": ["aws", "amazon web services"],
    "gcp": ["gcp", "google cloud"],
    "azure": ["azure"],
    "ci/cd": ["ci/cd", "ci", "cd", "pipelines"],
    "ios": ["ios"],
    "android": ["android"],
    "swift": ["swift"],
    "kotlin": ["kotlin"],
    "ocr": ["ocr"],
    "opencv": ["opencv"],
    "pytesseract": ["pytesseract", "tesseract"],
    "pdf": ["pdf"],
    "rest api": ["rest api", "rest", "api"],
    "celery": ["celery"],
}


PROFILE_RULES: dict[str, list[str]] = {
    "backend": ["python", "fastapi", "django", "flask", "sql", "postgresql", "redis"],
    "frontend": ["javascript", "typescript", "react", "vue"],
    "fullstack": ["python", "javascript", "react", "fastapi", "sql"],
    "data": ["pandas", "numpy", "machine learning", "tensorflow", "pytorch", "data analysis"],
    "devops": ["docker", "kubernetes", "linux", "aws", "gcp", "azure", "ci/cd"],
    "mobile": ["android", "ios", "swift", "kotlin"],
}


class ResumeJobMatcher:
    def normalize_text(self, text: str) -> str:
        return " ".join((text or "").lower().split())

    def extract_skills(self, resume_text: str) -> list[str]:
        text = self.normalize_text(resume_text)
        found: list[str] = []

        for canonical_skill, aliases in SKILL_ALIASES.items():
            for alias in aliases:
                if alias in text:
                    found.append(canonical_skill)
                    break

        return found

    def detect_profile(self, skills: list[str]) -> str:
        if not skills:
            return "general"

        best_profile = "general"
        best_score = 0

        for profile, profile_skills in PROFILE_RULES.items():
            score = sum(1 for skill in profile_skills if skill in skills)
            if score > best_score:
                best_score = score
                best_profile = profile

        return best_profile

    def extract_job_skills(self, job: dict[str, Any]) -> list[str]:
        text = self.normalize_text(
            " ".join([
                str(job.get("job_title", "")),
                str(job.get("company", "")),
                str(job.get("location", "")),
                str(job.get("salary", "")),
                str(job.get("source", "")),
            ])
        )

        found: list[str] = []
        for canonical_skill, aliases in SKILL_ALIASES.items():
            for alias in aliases:
                if alias in text:
                    found.append(canonical_skill)
                    break

        return found

    def match(
        self,
        jobs: list[dict[str, Any]],
        resume_text: str,
    ) -> tuple[list[str], list[dict[str, Any]]]:
        skills = self.extract_skills(resume_text)
        if not skills:
            return [], []

        profile = self.detect_profile(skills)
        matched: list[dict[str, Any]] = []

        for job in jobs:
            job_title = self.normalize_text(job.get("job_title", ""))
            job_company = self.normalize_text(job.get("company", ""))
            job_location = self.normalize_text(job.get("location", ""))
            job_source = self.normalize_text(job.get("source", ""))

            job_text = " ".join([
                job_title,
                job_company,
                job_location,
                job_source,
            ])

            matched_skills: list[str] = []
            score = 0

            for skill in skills:
                aliases = SKILL_ALIASES.get(skill, [skill])

                found_in_title = any(alias in job_title for alias in aliases)
                found_in_text = any(alias in job_text for alias in aliases)

                if found_in_title:
                    matched_skills.append(skill)
                    score += 5
                elif found_in_text:
                    matched_skills.append(skill)
                    score += 2

            if profile != "general" and profile in job_text:
                score += 3

            job_skills = self.extract_job_skills(job)
            missing_skills = [skill for skill in job_skills if skill not in skills]

            if score >= 4:
                job_copy = job.copy()
                job_copy["match_score"] = score
                job_copy["why_match"] = matched_skills
                job_copy["missing_skills"] = missing_skills[:5]
                job_copy["candidate_profile"] = profile
                matched.append(job_copy)

        matched.sort(
            key=lambda item: (
                item.get("match_score", 0),
                len(item.get("why_match", [])),
            ),
            reverse=True,
        )
        return skills, matched[:20]