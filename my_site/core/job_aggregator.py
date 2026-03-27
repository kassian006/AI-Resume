from __future__ import annotations

from typing import Any

from my_site.core.job_parsers.devkg import DevKGParser
from my_site.core.job_parsers.habr import HabrCareerParser
from my_site.core.job_parsers.head_hunter import HeadHunterParser
from my_site.core.job_parsers.job_lab import JobLabParser
from my_site.core.job_parsers.new_job import NewJobParser


class JobAggregator:
    def __init__(self) -> None:
        self.sources = [
            {
                "name": "devkg",
                "urls": [f"https://devkg.com/ru/jobs?page={page}" for page in range(1, 7)],
                "parser": DevKGParser(),
            },
            {
                "name": "headhunter",
                "urls": [f"https://bishkek.headhunter.kg/search/vacancy?page={page}" for page in range(0, 5)],
                "parser": HeadHunterParser(),
            },
            {
                "name": "joblab",
                "urls": ["https://joblab.kg/"],
                "parser": JobLabParser(),
            },
            {
                "name": "habr",
                "urls": [f"https://career.habr.com/vacancies?page={page}" for page in range(1, 6)],
                "parser": HabrCareerParser(),
            },
            {
                "name": "newjob",
                "urls": [f"https://newjob.kg/vacancies?page={page}" for page in range(1, 6)],
                "parser": NewJobParser(),
            },
        ]

    def collect_all_jobs(self) -> list[dict[str, Any]]:
        all_jobs: list[dict[str, Any]] = []

        for source in self.sources:
            parser = source["parser"]
            urls = source["urls"]

            for url in urls:
                try:
                    jobs = parser.parse(url)
                    all_jobs.extend(jobs)
                except Exception:
                    continue

        return self.remove_duplicates(all_jobs)

    def remove_duplicates(self, jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        unique_jobs: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()

        for job in jobs:
            key = (
                (job.get("job_title") or "").strip().lower(),
                (job.get("company") or "").strip().lower(),
                (job.get("url") or "").strip().lower(),
            )

            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)

        return unique_jobs