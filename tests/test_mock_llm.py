from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

from app.api import app, get_classifier
from app.llm import classify
from app.mock_llm import mock_classify
from app.schemas import Intent, Scope
from app.settings import MOCK_MODEL_NAME, ROOT
from eval.report import load_latest_report
from eval.run_eval import main


def triage_of(message: str) -> tuple[Intent, bool, str | None, Scope]:
    response = mock_classify(message)
    assert response.result is not None
    result = response.result
    return result.intent, result.is_emergency, result.neighborhood_raw, result.scope


def test_outage_with_neighborhood_and_wider_scope() -> None:
    intent, emergency, neighborhood, scope = triage_of("sem luz na rua toda aqui na Pituba")
    assert (intent, emergency, scope) == (Intent.OUTAGE, False, Scope.STREET_OR_AREA)
    assert neighborhood is not None
    assert neighborhood.lower() == "pituba"


def test_my_home_scope_is_detected() -> None:
    assert triage_of("so a minha casa ficou sem energia, moro no Rio Vermelho")[3] is Scope.MY_HOME


def test_typo_in_neighborhood_is_still_found() -> None:
    assert triage_of("sem luz aqui no Rio Vermlho")[2] == "rio vermlho"


def test_no_neighborhood_is_reported_as_none() -> None:
    assert triage_of("luz acabou")[2] is None


def test_emergency_keywords_and_extra_terms() -> None:
    assert triage_of("tem um fio caido na rua")[1]
    assert triage_of("o transformador esta soltando fumaça")[1]


@pytest.mark.parametrize(
    ("message", "intent"),
    [
        ("minha conta veio muito alta", Intent.BILLING),
        ("paguei e a luz continua cortada", Intent.RECONNECTION),
        ("qual o horario de atendimento da loja", Intent.OTHER),
    ],
)
def test_intents_other_than_outage(message: str, intent: Intent) -> None:
    assert triage_of(message)[0] is intent


def test_vague_message_has_low_confidence() -> None:
    result = mock_classify("oi").result
    assert result is not None
    assert result.confidence < 0.7


def test_response_is_marked_as_mock_and_free() -> None:
    response = mock_classify("sem luz")
    assert response.model == MOCK_MODEL_NAME
    assert (response.input_tokens, response.output_tokens) == (0, 0)


def test_api_uses_mock_classifier_only_in_mock_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_MODE", "mock")
    assert get_classifier() is mock_classify
    monkeypatch.setenv("LLM_MODE", "real")
    assert get_classifier() is classify


def test_endpoint_answers_end_to_end_in_mock_mode(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "demo.db"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    client = TestClient(app)
    known = client.post("/v1/triage", json={"message": "sem luz na pituba"}).json()
    emergency = client.post("/v1/triage", json={"message": "poste caiu na rua"}).json()
    assert known["action"] == "known_outage"
    assert emergency["action"] == "emergency"


def test_demo_eval_runs_without_key_and_writes_flagged_report(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert main(["--mock", "--split", "dev", "--output-dir", str(tmp_path)]) == 0
    report = load_latest_report(tmp_path)
    assert report is not None
    assert report.model == MOCK_MODEL_NAME
    markdown = next(tmp_path.glob("*.md")).read_text(encoding="utf-8")
    assert "MODO SIMULADO" in markdown


def test_eval_requires_model_unless_mock() -> None:
    with pytest.raises(SystemExit):
        main(["--split", "dev"])


def test_chat_shows_mock_banner_only_in_mock_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    script = str(ROOT / "ui" / "chat.py")
    monkeypatch.setenv("LLM_MODE", "mock")
    mocked = AppTest.from_file(script, default_timeout=30).run()
    assert any("MODO SIMULADO" in element.value for element in mocked.markdown)
    monkeypatch.setenv("LLM_MODE", "real")
    real = AppTest.from_file(script, default_timeout=30).run()
    assert not any("MODO SIMULADO" in element.value for element in real.markdown)
