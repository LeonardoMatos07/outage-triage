import json
import os
import urllib.error
import urllib.request

from app.schemas import TriageRequest, TriageResponse

DEFAULT_API_URL = "http://localhost:8000"
REQUEST_TIMEOUT_SECONDS = 60


class ApiUnavailableError(Exception):
    pass


def api_url() -> str:
    return os.environ.get("API_URL", DEFAULT_API_URL).rstrip("/")


def post_triage(message: str, session_id: str | None) -> TriageResponse:
    payload = TriageRequest(message=message, session_id=session_id).model_dump_json()
    request = urllib.request.Request(
        f"{api_url()}/v1/triage",
        data=payload.encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return TriageResponse.model_validate(json.load(response))
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        raise ApiUnavailableError from error
