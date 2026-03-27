from __future__ import annotations

import io
from typing import Any

from pypdf import PdfReader


def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    pages_text: list[str] = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            cleaned = text.strip()
            if cleaned:
                pages_text.append(cleaned)

    return "\n".join(pages_text).strip()


class ResumeParser:
    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        return extract_text_from_pdf_bytes(file_bytes)

    def parse_text(self, text: str) -> dict[str, Any]:
        return {
            "raw_preview": text[:1000],
            "char_count": len(text),
            "word_count": len(text.split()),
        }

    def is_text_usable(self, text: str, min_chars: int = 80) -> bool:
        if not isinstance(text, str):
            return False

        cleaned = " ".join(text.split()).strip()
        if len(cleaned) < min_chars:
            return False

        letters = sum(1 for ch in cleaned if ch.isalpha())
        return letters >= min_chars // 2