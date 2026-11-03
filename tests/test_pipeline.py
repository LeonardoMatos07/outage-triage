import sqlite3

import anthropic
import httpx2
from fastapi.testclient import TestClient

from app.api import app, get_classifier, get_connection
from app.llm import LlmResponse
from app.pipeline import run_triage
from app.schemas import Action, HandoffReason, Priority, Queue
from tests.conftest import ScriptedClassifier, make_triage


def test_known_outage_replies_with_registered_protocol(connection: sqlite3.Connection) -> None:
    classifier = ScriptedClassifier(make_triage(neighborhood_raw="pituba"))
    response = run_triage(connection, "sem luz na pituba", classifier=classifier)
    assert response.action is Action.KNOWN_OUTAGE
    assert response.protocol == "OC-0001"
    assert "OC-0001" in response.reply
    assert "03/11 às 14:00" in response.reply
    assert not response.handed_to_human


def test_individual_ticket_is_opened_for_my_home(connection: sqlite3.Connection) -> None:
    classifier = ScriptedClassifier(make_triage(neighborhood_raw="Brotas", scope="my_home"))
    response = run_triage(connection, "so minha casa sem luz", classifier=classifier)
    assert response.action is Action.TICKET_MY_HOME
    assert response.protocol == "CH-000001"
    assert "disjuntor" in response.reply


def test_possible_new_outage_ticket_is_opened(connection: sqlite3.Connection) -> None:
    classifier = ScriptedClassifier(make_triage(neighborhood_raw="Brotas", scope="unknown"))
    response = run_triage(connection, "sem luz em brotas", classifier=classifier)
    assert response.action is Action.TICKET_POSSIBLE_NEW_OUTAGE
    assert "possível nova ocorrência" in response.reply
    assert connection.execute("SELECT COUNT(*) FROM tickets").fetchone()[0] == 1


def test_keyword_emergency_overrides_llm_saying_no(connection: sqlite3.Connection) -> None:
    classifier = ScriptedClassifier(make_triage(is_emergency=False))
    response = run_triage(connection, "tem um fio caido aqui", classifier=classifier)
    assert response.action is Action.EMERGENCY
    assert response.priority is Priority.MAX
    assert response.queue is Queue.EMERGENCY
    assert "não se aproxime" in response.reply


def test_llm_emergency_counts_without_keyword(connection: sqlite3.Connection) -> None:
    classifier = ScriptedClassifier(make_triage(is_emergency=True))
    response = run_triage(connection, "tem algo estranho no poste", classifier=classifier)
    assert response.action is Action.EMERGENCY


def test_emergency_survives_llm_returning_nothing(connection: sqlite3.Connection) -> None:
    response = run_triage(connection, "poste caiu na rua", classifier=ScriptedClassifier(None))
    assert response.action is Action.EMERGENCY


def test_llm_api_failure_hands_off_to_human(connection: sqlite3.Connection) -> None:
    def failing_classifier(message: str) -> LlmResponse:
        raise anthropic.APIConnectionError(request=httpx2.Request("POST", "https://example.test"))

    response = run_triage(connection, "estou sem luz", classifier=failing_classifier)
    assert response.handoff_reason is HandoffReason.LLM_FAILURE
    assert response.handed_to_human


def test_billing_goes_to_billing_queue(connection: sqlite3.Connection) -> None:
    classifier = ScriptedClassifier(make_triage(intent="billing", neighborhood_raw=None))
    response = run_triage(connection, "minha conta veio alta", classifier=classifier)
    assert response.queue is Queue.BILLING
    assert "contas" in response.reply


def test_neighborhood_is_asked_once_then_handed_off(connection: sqlite3.Connection) -> None:
    classifier = ScriptedClassifier(
        make_triage(neighborhood_raw=None), make_triage(neighborhood_raw="perto do mercado")
    )
    first = run_triage(connection, "sem luz", classifier=classifier)
    assert first.action is Action.ASK_NEIGHBORHOOD
    second = run_triage(connection, "perto do mercado", first.session_id, classifier)
    assert second.handoff_reason is HandoffReason.NEIGHBORHOOD_NOT_IDENTIFIED
    assert second.queue is Queue.OUTAGE


def test_followup_message_is_combined_with_the_pending_one(
    connection: sqlite3.Connection,
) -> None:
    classifier = ScriptedClassifier(
        make_triage(neighborhood_raw=None), make_triage(neighborhood_raw="Pituba")
    )
    first = run_triage(connection, "estou sem luz", classifier=classifier)
    second = run_triage(connection, "Pituba", first.session_id, classifier)
    assert classifier.received[1] == "estou sem luz\nPituba"
    assert second.action is Action.KNOWN_OUTAGE


def test_session_is_cleared_after_resolution(connection: sqlite3.Connection) -> None:
    classifier = ScriptedClassifier(make_triage(neighborhood_raw=None), make_triage())
    first = run_triage(connection, "sem luz", classifier=classifier)
    run_triage(connection, "Pituba", first.session_id, classifier)
    assert connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0


def test_every_attendance_is_logged(connection: sqlite3.Connection) -> None:
    classifier = ScriptedClassifier(make_triage(intent="billing"))
    run_triage(connection, "minha conta veio alta", classifier=classifier)
    (row,) = connection.execute("SELECT * FROM attendances").fetchall()
    assert row["message"] == "minha conta veio alta"
    assert row["action"] == "handoff"
    assert row["handed_to_human"] == 1
    assert row["handoff_reason"] == "unsupported_intent"
    assert row["model"] == "test-model"
    assert (row["input_tokens"], row["output_tokens"]) == (120, 30)
    assert row["cost_brl"] is None
    assert row["latency_seconds"] == 0.5
    assert '"intent":"billing"' in row["triage_result"]


def test_simulation_notice_is_always_present(connection: sqlite3.Connection) -> None:
    response = run_triage(connection, "sem luz", classifier=ScriptedClassifier(make_triage()))
    assert "simuladas" in response.notice


def test_triage_endpoint(connection: sqlite3.Connection) -> None:
    classifier = ScriptedClassifier(make_triage(neighborhood_raw="Pituba"))
    app.dependency_overrides[get_connection] = lambda: connection
    app.dependency_overrides[get_classifier] = lambda: classifier
    try:
        response = TestClient(app).post("/v1/triage", json={"message": "sem luz na pituba"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["action"] == "known_outage"
    assert body["protocol"] == "OC-0001"
    assert body["session_id"]


def test_endpoint_rejects_empty_message() -> None:
    assert TestClient(app).post("/v1/triage", json={"message": ""}).status_code == 422
