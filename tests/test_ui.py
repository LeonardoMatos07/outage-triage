import io
import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from app.schemas import Action, HandoffReason, Priority, Queue, TriageResponse
from ui import client
from ui.view import build_details, outcome_label


def make_response(**overrides: Any) -> TriageResponse:
    fields: dict[str, Any] = {
        "session_id": "s",
        "reply": "ok",
        "action": Action.KNOWN_OUTAGE,
        "handed_to_human": False,
        "handoff_reason": None,
        "queue": None,
        "priority": None,
        "protocol": "OC-0001",
        "notice": "simuladas",
    }
    return TriageResponse(**{**fields, **overrides})


def test_details_include_only_present_fields() -> None:
    details = build_details(make_response())
    assert details == {"Ação": "known_outage", "Protocolo": "OC-0001"}


def test_details_show_handoff_information() -> None:
    response = make_response(
        action=Action.EMERGENCY,
        handed_to_human=True,
        handoff_reason=HandoffReason.EMERGENCY,
        queue=Queue.EMERGENCY,
        priority=Priority.MAX,
        protocol=None,
    )
    details = build_details(response)
    assert details["Fila"] == "emergency"
    assert details["Prioridade"] == "max"
    assert details["Motivo do encaminhamento"] == "emergency"
    assert "Protocolo" not in details


def test_outcome_label_depends_on_handoff() -> None:
    assert outcome_label(make_response()) == "Resolvido automaticamente"
    assert outcome_label(make_response(handed_to_human=True)) == "Encaminhado para atendente"


def test_post_triage_sends_message_and_parses_response(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: float) -> io.BytesIO:
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data)
        return io.BytesIO(make_response().model_dump_json().encode("utf-8"))

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setenv("API_URL", "http://api:8000/")
    response = client.post_triage("sem luz", "abc")
    assert captured["url"] == "http://api:8000/v1/triage"
    assert captured["body"] == {"message": "sem luz", "session_id": "abc"}
    assert response.protocol == "OC-0001"


def test_post_triage_wraps_connection_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing_urlopen(request: Any, timeout: float) -> io.BytesIO:
        raise urllib.error.URLError("down")

    monkeypatch.setattr(urllib.request, "urlopen", failing_urlopen)
    with pytest.raises(client.ApiUnavailableError):
        client.post_triage("sem luz", None)
