from __future__ import annotations

from typing import Any

from my_site.core.job_parsers.base_parse import BaseJobParser


class JobLabParser(BaseJobParser):
    SOURCE_NAME = "joblab"

    def parse(self, url: str) -> list[dict[str, Any]]:
        html = self.fetch_html(url)
        soup = self.make_soup(html)

        jobs: list[dict[str, Any]] = []
        rows = soup.find_all("tr")

        for row in rows:
            title_cell = row.find("td", class_="td-to-div")
            salary_cell = row.find("td", class_="td-to-div-zp")
            location_cell = row.find("td", class_="td-to-div-city")

            if not title_cell:
                continue

            title_tag = title_cell.find("a", href=True)
            if not title_tag:
                continue

            href = title_tag.get("href", "")
            if "/vacancy/" not in href:
                continue

            job_title = self.clean_text(title_tag.get_text())
            salary = self.clean_text(salary_cell.get_text()) if salary_cell else "Не указана"
            location = self.clean_text(location_cell.get_text()) if location_cell else "Не указана"
            job_url = self.absolute_url("https://joblab.kg", href)

            if not job_title:
                continue

            jobs.append({
                "job_title": job_title,
                "company": "",
                "salary": salary,
                "location": location,
                "source": self.SOURCE_NAME,
                "url": job_url,
                "remote": False,
                "visa_support": False,
                "match_score": 0,
                "why_match": [],
            })

        return jobs