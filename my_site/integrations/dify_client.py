from __future__ import annotations

from typing import Any
import json
import re
import httpx
from my_site.config import DIFY_API_KEY, DIFY_BASE_URL


class DifyClient:
    def __init__(self):
        self.base_url = (DIFY_BASE_URL or "").rstrip("/")
        self.api_key = (DIFY_API_KEY or "").strip()

        if not self.base_url:
            raise ValueError("DIFY_BASE_URL is not configured")
        if not self.api_key:
            raise ValueError("DIFY_API_KEY is not configured")

    def analyze_resume(self, resume_text: str) -> dict[str, Any]:
        url = f"{self.base_url}/workflows/run"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "inputs": {
                "resume_text": resume_text,
            },
            "response_mode": "blocking",
            "user": "resume-backend",
        }

        with httpx.Client(timeout=180.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    def extract_result_json(self, dify_response: dict[str, Any]) -> dict[str, Any]:
        outputs = dify_response.get("data", {}).get("outputs", {})
        raw_result = outputs.get("result")

        if raw_result is None:
            raise ValueError("Dify response does not contain data.outputs.result")

        if isinstance(raw_result, dict):
            return raw_result

        if not isinstance(raw_result, str):
            raise ValueError(f"Unsupported Dify result format: {type(raw_result)!r}")

        text = raw_result.strip()

        fenced_match = re.match(
            r"^```(?:json)?\s*(.*?)\s*```$",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if fenced_match:
            text = fenced_match.group(1).strip()

        try:
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                raise ValueError("Dify JSON result is not an object")
            return parsed
        except json.JSONDecodeError:
            pass

        # fallback: try to extract the first JSON object from the text
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start:end + 1]
            parsed = json.loads(candidate)
            if not isinstance(parsed, dict):
                raise ValueError("Dify extracted JSON is not an object")
            return parsed

        raise ValueError(f"Failed to parse Dify result JSON: {raw_result}")