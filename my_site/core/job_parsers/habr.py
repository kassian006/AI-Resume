from __future__ import annotations

import re
from typing import Any

from my_site.core.job_parsers.base_parse import BaseJobParser


class HabrCareerParser(BaseJobParser):
    SOURCE_NAME = "habr"

    def parse(self, url: str) -> list[dict[str, Any]]:
        html = self.fetch_html(url)
        soup = self.make_soup(html)

        jobs: list[dict[str, Any]] = []
        cards = soup.select("div.vacancy-card")

        for card in cards:
            title_tag = card.find("div", class_="vacancy-card__title")
            company_tag = card.find("div", class_="vacancy-card__company")
            salary_tag = card.find("h4", class_="predicted-salary__title")
            link_tag = card.find(
                "a",
                href=lambda x: x and x.startswith("/vacancies/") and "/skills/" not in x
            )

            job_title = self.clean_text(title_tag.get_text()) if title_tag else ""
            company = self.clean_text(company_tag.get_text()) if company_tag else ""
            salary = self.clean_text(salary_tag.get_text()) if salary_tag else "Не указана"
            job_url = self.absolute_url("https://career.habr.com", link_tag.get("href")) if link_tag else ""

            company = re.sub(r"\d+\.\d+\s*$", "", company).strip() or "Не указана"
            location = "Не указана"

            meta_block = card.find("div", class_="vacancy-card__meta")
            if meta_block:
                spans = meta_block.find_all("span", class_="chip-with-icon__text")
                for span in spans:
                    text = self.clean_text(span.get_text())
                    if text:
                        location = text
                        break

            if not job_title:
                continue

            jobs.append({
                "job_title": job_title,
                "company": company,
                "salary": salary or "Не указана",
                "location": location,
                "source": self.SOURCE_NAME,
                "url": job_url,
                "remote": "удал" in location.lower() or "remote" in location.lower(),
                "visa_support": False,
                "match_score": 0,
                "why_match": [],
            })

        return jobs