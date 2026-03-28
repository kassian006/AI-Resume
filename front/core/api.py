from typing import Any
import requests

from core.config import API_BASE_URL


def api_request(
    method: str,
    path: str,
    token: str | None = None,
    json_data: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
):
    url = f"{API_BASE_URL}{path}"

    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.request(
        method=method,
        url=url,
        headers=headers,
        json=json_data,
        files=files,
        timeout=120,
    )

    try:
        data = response.json()
    except Exception:
        data = {"detail": response.text}

    if not response.ok:
        raise Exception(data.get("detail", "Request failed"))

    return data


def register_user(email: str, password: str):
    return api_request(
        "POST",
        "/auth/register/",
        json_data={"email": email, "password": password},
    )


def login_user(email: str, password: str):
    return api_request(
        "POST",
        "/auth/login/",
        json_data={"email": email, "password": password},
    )


def get_me(token: str):
    return api_request("GET", "/auth/me", token=token)


def get_sessions(token: str):
    return api_request("GET", "/resumes/sessions", token=token)


def get_session_detail(token: str, session_id: int):
    return api_request("GET", f"/resumes/sessions/{session_id}", token=token)


def upload_resume(token: str, uploaded_file):
    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            "application/pdf",
        )
    }
    return api_request("POST", "/resumes/upload", token=token, files=files)


def match_jobs_from_resume(uploaded_file):
    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            "application/pdf",
        )
    }
    return api_request("POST", "/jobs/match-from-file", files=files)