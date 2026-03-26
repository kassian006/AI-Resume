from __future__ import annotations

from typing import Any

import httpx

from my_site.config import OCR_BASE_URL, OCR_API_KEY


class OCRClient:
    def __init__(self, base_url: str = OCR_BASE_URL, api_key: str = OCR_API_KEY):
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = (api_key or "").strip()

        if not self.base_url:
            raise ValueError("OCR_BASE_URL is not configured")

    def extract_file(
        self,
        file_bytes: bytes,
        filename: str,
        lang: str = "rus+eng",
    ) -> dict[str, Any]:
        files = {
            "file": (filename, file_bytes, "application/pdf"),
        }

        headers: dict[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        with httpx.Client(timeout=180.0) as client:
            response = client.post(
                f"{self.base_url}/ocr/file",
                params={"lang": lang},
                files=files,
                headers=headers,
            )

        if response.status_code >= 400:
            raise RuntimeError(
                f"OCR request failed: status={response.status_code}, body={response.text}"
            )

        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("OCR response is not a JSON object")

        text = data.get("text")
        if not isinstance(text, str):
            raise ValueError("OCR response does not contain valid 'text'")

        return data