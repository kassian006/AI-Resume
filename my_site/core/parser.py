from __future__ import annotations

import io
from typing import Any

from pypdf import PdfReader


class ResumeParser:
    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        reader = PdfReader(io.BytesIO(file_bytes))
        pages_text: list[str] = []

        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)

        return "\n".join(pages_text).strip()

    def parse_text(self, text: str) -> dict[str, Any]:
        return {
            "raw_preview": text[:1000],
            "char_count": len(text),
            "word_count": len(text.split()),
        }