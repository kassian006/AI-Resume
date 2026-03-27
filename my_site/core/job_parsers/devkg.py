from __future__ import annotations

from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


class BaseJobParser:
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/127.0.0.0 Safari/537.36"
        )
    }

    def fetch_html(self, url: str) -> str:
        response = requests.get(url, headers=self.HEADERS, timeout=20)
        response.raise_for_status()
        return response.text

    def make_soup(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "html.parser")

    def clean_text(self, text: str) -> str:
        return " ".join(text.replace("\xa0", " ").split())

    def absolute_url(self, base_url: str, relative_url: str | None) -> str:
        if not relative_url:
            return ""
        return urljoin(base_url, relative_url)