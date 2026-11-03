import pytest
from streamlit.testing.v1 import AppTest

from app.schemas import Action, TriageResponse
from app.settings import ROOT
from eval import report as report_module
from eval.dataset import DEV_PATH, load_examples
from eval.report import EvalReport
from eval.run_eval import evaluate_model
from tests.test_eval_run import OracleClassifier
from ui import client

APP_TIMEOUT_SECONDS = 30


def chat_app() -> AppTest:
    return AppTest.from_file(str(ROOT / "ui" / "chat.py"), default_timeout=APP_TIMEOUT_SECONDS)


def dashboard_app() -> AppTest:
    return AppTest.from_file(str(ROOT / "ui" / "dashboard.py"), default_timeout=APP_TIMEOUT_SECONDS)


def sample_reports() -> list[EvalReport]:
    examples = load_examples(DEV_PATH)[:10]
    return [
        evaluate_model(model, "dev", examples, 0, OracleClassifier(examples, model))
        for model in ("claude-haiku-5-5", "claude-sonnet-5-5")
    ]


def test_chat_shows_welcome_and_simulation_notice() -> None:
    app = chat_app().run()
    assert not app.exception
    assert "simuladas" in app.warning[0].value
    assert app.chat_message[0].markdown[0].value.startswith("Olá!")


def test_chat_sends_message_and_shows_reply(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(message: str, session_id: str | None) -> TriageResponse:
        return TriageResponse(
            session_id="s1",
            reply="Já temos uma ocorrência registrada.",
            action=Action.KNOWN_OUTAGE,
            handed_to_human=False,
            handoff_reason=None,
            queue=None,
            priority=None,
            protocol="OC-0001",
            notice="simuladas",
        )

    monkeypatch.setattr(client, "post_triage", fake_post)
    app = chat_app().run()
    app.chat_input[0].set_value("sem luz na pituba").run()
    assert not app.exception
    replies = [message.markdown[0].value for message in app.chat_message]
    assert replies[-2:] == ["sem luz na pituba", "Já temos uma ocorrência registrada."]


def test_chat_shows_error_when_api_is_down(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing_post(message: str, session_id: str | None) -> TriageResponse:
        raise client.ApiUnavailableError

    monkeypatch.setattr(client, "post_triage", failing_post)
    app = chat_app().run()
    app.chat_input[0].set_value("sem luz").run()
    assert "Não foi possível" in app.chat_message[-1].markdown[0].value


def test_dashboard_without_reports_asks_to_run_eval(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(report_module, "load_reports", lambda directory=None: [])
    app = dashboard_app().run()
    assert not app.exception
    assert "make eval" in app.info[0].value


def test_dashboard_reads_latest_report(monkeypatch: pytest.MonkeyPatch) -> None:
    reports = sample_reports()
    monkeypatch.setattr(report_module, "load_reports", lambda directory=None: reports)
    app = dashboard_app().run()
    assert not app.exception
    assert "simuladas" in app.warning[0].value
    subheaders = [subheader.value for subheader in app.subheader]
    assert "Métricas" in subheaders
    assert "Comparação de modelos" in subheaders
    assert len(app.table) == 3
