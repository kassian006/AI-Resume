from __future__ import annotations

from typing import Any

from my_site.core.job_parsers.base_parse import BaseJobParser


class DevKGParser(BaseJobParser):
    SOURCE_NAME = "devkg"

    def parse(self, url: str) -> list[dict[str, Any]]:
        html = self.fetch_html(url)
        soup = self.make_soup(html)

        jobs: list[dict[str, Any]] = []
        cards = soup.find_all("article", class_="item")

        for card in cards:
            info = card.find("div", class_="information")
            if not info:
                continue

            title_tag = info.find("div", class_="jobs-item-field position")
            company_tag = info.find("div", class_="jobs-item-field company")
            salary_tag = info.find("div", class_="jobs-item-field price")
            location_tag = info.find("div", class_="jobs-item-field type")
            link_tag = card.find("a", class_="link")

            job_title = ""
            company = ""
            salary = "Не указана"
            location = "Не указана"

            if title_tag:
                span = title_tag.find("span")
                if span:
                    span.decompose()
                job_title = self.clean_text(title_tag.get_text())

            if company_tag:
                span = company_tag.find("span")
                if span:
                    span.decompose()
                company = self.clean_text(company_tag.get_text())

            if salary_tag:
                span = salary_tag.find("span")
                if span:
                    span.decompose()
                text = self.clean_text(salary_tag.get_text())
                if text:
                    salary = text

            if location_tag:
                span = location_tag.find("span")
                if span:
                    span.decompose()
                text = self.clean_text(location_tag.get_text())
                if text:
                    location = text

            job_url = self.absolute_url("https://devkg.com", link_tag.get("href")) if link_tag else ""

            if not job_title:
                continue

            jobs.append({
                "job_title": job_title,
                "company": company,
                "salary": salary,
                "location": location,
                "source": self.SOURCE_NAME,
                "url": job_url,
                "remote": "удал" in location.lower(),
                "visa_support": False,
                "match_score": 0,
                "why_match": [],
            })

        return jobs