from collections.abc import Callable

import pytest
from streamlit.testing.v1 import AppTest

from app.schemas import Action, HandoffReason, Priority, Queue, TriageResponse
from app.settings import ROOT
from app.texts import load_texts
from eval import report as report_module
from eval.dataset import DEV_PATH, load_examples
from eval.report import EvalReport
from eval.run_eval import evaluate_model
from tests.test_eval_run import OracleClassifier
from ui import client
from ui.view import UI_TEXTS

APP_TIMEOUT_SECONDS = 30
EXAMPLES = load_texts(UI_TEXTS)["chat"]["examples"]


def chat_app() -> AppTest:
    return AppTest.from_file(str(ROOT / "ui" / "chat.py"), default_timeout=APP_TIMEOUT_SECONDS)


def dashboard_app() -> AppTest:
    return AppTest.from_file(str(ROOT / "ui" / "dashboard.py"), default_timeout=APP_TIMEOUT_SECONDS)


def page_html(app: AppTest) -> str:
    return "\n".join(element.value for element in app.markdown)


def example_buttons(app: AppTest) -> list[str]:
    return [button.label for button in app.button if (button.key or "").startswith("example_")]


def sample_reports() -> list[EvalReport]:
    examples = load_examples(DEV_PATH)
    return [
        evaluate_model(model, "dev", examples, 0, OracleClassifier(examples, model))
        for model in ("claude-haiku-5-5", "claude-sonnet-5-5")
    ]


def make_response(**overrides: object) -> TriageResponse:
    fields: dict[str, object] = {
        "session_id": "s1",
        "reply": "Já temos uma ocorrência registrada.",
        "action": Action.KNOWN_OUTAGE,
        "handed_to_human": False,
        "handoff_reason": None,
        "queue": None,
        "priority": None,
        "protocol": "OC-0001",
        "notice": "simuladas",
    }
    return TriageResponse.model_validate({**fields, **overrides})


def fake_post(response: TriageResponse) -> Callable[[str, str | None], TriageResponse]:
    def post(message: str, session_id: str | None) -> TriageResponse:
        return response

    return post


def test_chat_shows_identity_welcome_notice_and_examples() -> None:
    app = chat_app().run()
    assert not app.exception
    html = page_html(app)
    assert "Distribuidora Exemplo" in html
    assert "empresa fictícia" in html
    assert "simuladas" in html
    assert "Olá!" in app.chat_message[0].markdown[0].value
    assert example_buttons(app) == EXAMPLES


def test_chat_has_no_mock_banner_in_real_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_MODE", "real")
    assert "MODO SIMULADO" not in page_html(chat_app().run())


def test_chat_shows_mock_banner_in_mock_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_MODE", "mock")
    assert "MODO SIMULADO" in page_html(chat_app().run())


def test_example_chip_sends_the_message(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[str] = []

    def recording_post(message: str, session_id: str | None) -> TriageResponse:
        sent.append(message)
        return make_response()

    monkeypatch.setattr(client, "post_triage", recording_post)
    app = chat_app().run()
    app.button(key="example_0").click().run()
    assert not app.exception
    assert sent == [EXAMPLES[0]]
    assert app.chat_message[1].markdown[0].value == EXAMPLES[0]
    assert "Já temos uma ocorrência registrada." in page_html(app)


def test_automatic_reply_shows_badge_and_prominent_protocol(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(client, "post_triage", fake_post(make_response()))
    app = chat_app().run()
    app.chat_input[0].set_value("sem luz na pituba").run()
    reply = app.chat_message[-1].markdown[0].value
    assert "dx-reply--automatic" in reply
    assert "Resolvido automaticamente" in reply
    assert "dx-protocol__code" in reply
    assert "OC-0001" in reply


def test_emergency_reply_is_visually_distinct(monkeypatch: pytest.MonkeyPatch) -> None:
    response = make_response(
        reply="ATENÇÃO: não se aproxime.",
        action=Action.EMERGENCY,
        handed_to_human=True,
        handoff_reason=HandoffReason.EMERGENCY,
        queue=Queue.EMERGENCY,
        priority=Priority.MAX,
        protocol=None,
    )
    monkeypatch.setattr(client, "post_triage", fake_post(response))
    app = chat_app().run()
    app.chat_input[0].set_value("fio caido na rua").run()
    reply = app.chat_message[-1].markdown[0].value
    assert "dx-reply--emergency" in reply
    assert "dx-badge--emergency" in reply
    assert "Emergência" in reply
    assert "dx-protocol" not in reply


def test_handoff_and_question_badges(monkeypatch: pytest.MonkeyPatch) -> None:
    handoff = make_response(
        action=Action.HANDOFF,
        handed_to_human=True,
        handoff_reason=HandoffReason.UNSUPPORTED_INTENT,
        queue=Queue.BILLING,
        protocol=None,
    )
    monkeypatch.setattr(client, "post_triage", fake_post(handoff))
    app = chat_app().run()
    app.chat_input[0].set_value("minha conta veio alta").run()
    assert "dx-reply--handoff" in app.chat_message[-1].markdown[0].value
    question = make_response(action=Action.ASK_NEIGHBORHOOD, protocol=None)
    monkeypatch.setattr(client, "post_triage", fake_post(question))
    app = chat_app().run()
    app.chat_input[0].set_value("luz acabou").run()
    assert "dx-reply--question" in app.chat_message[-1].markdown[0].value


def test_technical_details_are_kept_in_a_collapsed_panel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client, "post_triage", fake_post(make_response()))
    app = chat_app().run()
    app.chat_input[0].set_value("sem luz na pituba").run()
    assert any("Detalhes técnicos" in expander.label for expander in app.expander)
    assert "dx-kv" in page_html(app)


def test_examples_are_collapsed_after_the_first_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client, "post_triage", fake_post(make_response()))
    app = chat_app().run()
    app.chat_input[0].set_value("sem luz").run()
    assert any("Mensagens de exemplo" in expander.label for expander in app.expander)


def test_new_conversation_button_resets_the_chat(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client, "post_triage", fake_post(make_response()))
    app = chat_app().run()
    app.chat_input[0].set_value("sem luz").run()
    assert len(app.chat_message) == 3
    app.button(key="new_conversation").click().run()
    assert len(app.chat_message) == 1


def test_chat_shows_error_when_api_is_down(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing_post(message: str, session_id: str | None) -> TriageResponse:
        raise client.ApiUnavailableError

    monkeypatch.setattr(client, "post_triage", failing_post)
    app = chat_app().run()
    app.chat_input[0].set_value("sem luz").run()
    assert "Não foi possível" in app.chat_message[-1].markdown[0].value


def test_dashboard_empty_state_explains_how_to_generate_a_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_MODE", "real")
    monkeypatch.setattr(report_module, "load_reports", lambda directory=None: [])
    app = dashboard_app().run()
    assert not app.exception
    html = page_html(app)
    assert "dx-empty" in html
    assert "make eval" in html
    assert "simuladas" in html


def test_dashboard_empty_state_in_mock_mode_points_to_demo_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setattr(report_module, "load_reports", lambda directory=None: [])
    html = page_html(dashboard_app().run())
    assert "make demo-report" in html
    assert "MODO SIMULADO" in html


def test_dashboard_leads_with_safety_and_shows_kpi_cards(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_MODE", "real")
    reports = sample_reports()
    monkeypatch.setattr(report_module, "load_reports", lambda directory=None: reports)
    app = dashboard_app().run()
    assert not app.exception
    html = page_html(app)
    assert html.index("Segurança primeiro") < html.index("Qualidade da triagem")
    assert html.index("Qualidade da triagem") < html.index("Operação e custo")
    assert html.count('class="dx-card ') == 9
    assert "dx-card--hero" in html
    assert "Recall de emergência" in html
    assert "premissas do autor" in html
    assert "simuladas" in html
    assert "MODO SIMULADO" not in html


def test_dashboard_shows_comparison_and_confusion_matrix(monkeypatch: pytest.MonkeyPatch) -> None:
    reports = sample_reports()
    monkeypatch.setattr(report_module, "load_reports", lambda directory=None: reports)
    html = page_html(dashboard_app().run())
    assert "Comparação de modelos" in html
    assert "claude-sonnet-5-5" in html
    assert "dx-best" in html
    assert "Matriz de confusão" in html
    assert "dx-cm" in html


def test_dashboard_shows_mock_banner_in_mock_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_MODE", "mock")
    reports = sample_reports()
    monkeypatch.setattr(report_module, "load_reports", lambda directory=None: reports)
    assert "MODO SIMULADO" in page_html(dashboard_app().run())
