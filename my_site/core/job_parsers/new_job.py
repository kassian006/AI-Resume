from __future__ import annotations

from typing import Any

from my_site.core.job_parsers.base_parse import BaseJobParser


class NewJobParser(BaseJobParser):
    SOURCE_NAME = "newjob"

    def parse(self, url: str) -> list[dict[str, Any]]:
        html = self.fetch_html(url)
        soup = self.make_soup(html)

        jobs: list[dict[str, Any]] = []
        cards = soup.find_all("div", attrs={"data-type": "vacancy"})

        for card in cards:
            title_tag = card.find("div", class_="c-job-teaser__title")
            company_tag = card.find("div", class_="c-job-teaser__company-name")
            location_tag = card.find("div", class_="c-job-teaser__cities")
            salary_tag = card.find("div", class_="c-job-teaser__salary")
            link_tag = card.find("a", class_="c-job-teaser__info-link")

            job_title = self.clean_text(title_tag.get_text()) if title_tag else ""
            company = self.clean_text(company_tag.get_text()) if company_tag else "Не указана"
            location = self.clean_text(location_tag.get_text()) if location_tag else "Не указана"
            salary = self.clean_text(salary_tag.get_text()) if salary_tag else "Не указана"
            job_url = self.absolute_url("https://newjob.kg", link_tag.get("href")) if link_tag else ""

            salary = salary.replace("Новая вакансия", "").strip() or "Не указана"

            if not job_title:
                continue

            jobs.append({
                "job_title": job_title,
                "company": company,
                "salary": salary,
                "location": location,
                "source": self.SOURCE_NAME,
                "url": job_url,
                "remote": "удал" in location.lower() or "remote" in location.lower(),
                "visa_support": False,
                "match_score": 0,
                "why_match": [],
            })

        return jobs