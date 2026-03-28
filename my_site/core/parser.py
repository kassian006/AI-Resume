from __future__ import annotations

import io
from typing import Any

from pypdf import PdfReader

from my_site.integrations.ocr_client import OCRClient


def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        pages_text: list[str] = []

        for page in reader.pages:
            text = page.extract_text()
            if text:
                cleaned = text.strip()
                if cleaned:
                    pages_text.append(cleaned)

        return "\n".join(pages_text).strip()
    except Exception:
        return ""


class ResumeParser:
    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        return extract_text_from_pdf_bytes(file_bytes)

    def parse_text(self, text: str) -> dict[str, Any]:
        cleaned = " ".join((text or "").split()).strip()
        return {
            "raw_preview": cleaned[:1000],
            "char_count": len(cleaned),
            "word_count": len(cleaned.split()),
        }

    def is_text_usable(self, text: str, min_chars: int = 80) -> bool:
        if not isinstance(text, str):
            return False

        cleaned = " ".join(text.split()).strip()
        if len(cleaned) < min_chars:
            return False

        letters = sum(1 for ch in cleaned if ch.isalpha())
        return letters >= min_chars // 2

    def extract_text_smart(
        self,
        file_bytes: bytes,
        filename: str,
        lang: str = "rus+eng",
    ) -> tuple[str, str]:
        pdf_text = self.extract_text_from_pdf(file_bytes)

        if self.is_text_usable(pdf_text):
            return pdf_text, "pdf_text"

        ocr_client = OCRClient()
        ocr_result = ocr_client.extract_file(
            file_bytes=file_bytes,
            filename=filename,
            lang=lang,
        )
        ocr_text = (ocr_result.get("text") or "").strip()

        if self.is_text_usable(ocr_text):
            return ocr_text, "ocr"

        return "", "ocr"