import sqlite3
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from app.database import connect, initialize
from app.mock_llm import mock_classify
from app.pipeline import run_triage
from app.schemas import Action, HandoffReason
from app.settings import ROOT
from app.texts import load_texts
from eval.live_stats import load_live_stats
from tests.conftest import ScriptedClassifier, make_triage
from ui.live_view import bars_html, primary_kpis, recent_table_html, secondary_kpis
from ui.view import UI_TEXTS


def populate(connection: sqlite3.Connection) -> None:
    run_triage(connection, "sem luz na pituba", classifier=mock_classify)
    run_triage(connection, "fio caido na rua", classifier=mock_classify)
    run_triage(connection, "minha conta veio alta", classifier=mock_classify)
    run_triage(connection, "luz acabou", classifier=mock_classify)


def test_empty_database_has_no_attendances(connection: sqlite3.Connection) -> None:
    stats = load_live_stats(connection)
    assert stats.total == 0
    assert stats.auto_resolution.value is None
    assert stats.average_cost_brl is None
    assert stats.latency.median_seconds is None
    assert stats.recent == []


def test_counts_actions_reasons_and_emergencies(connection: sqlite3.Connection) -> None:
    populate(connection)
    stats = load_live_stats(connection)
    assert stats.total == 4
    assert stats.emergencies == 1
    assert stats.handed_to_human == 2
    assert (stats.auto_resolution.correct, stats.auto_resolution.total) == (2, 4)
    assert stats.by_action["known_outage"] == 1
    assert stats.by_action["ask_neighborhood"] == 1
    assert stats.by_handoff_reason == {"emergency": 1, "unsupported_intent": 1}


def test_recent_attendances_are_newest_first_and_limited(connection: sqlite3.Connection) -> None:
    populate(connection)
    stats = load_live_stats(connection, recent_limit=2)
    assert [entry.message for entry in stats.recent] == ["luz acabou", "minha conta veio alta"]


def test_cost_is_averaged_when_every_attendance_has_a_price(
    connection: sqlite3.Connection,
) -> None:
    classifier = ScriptedClassifier(make_triage(), make_triage())
    run_triage(connection, "sem luz", classifier=classifier)
    run_triage(connection, "sem luz de novo", classifier=classifier)
    connection.execute("UPDATE attendances SET cost_brl = 0.002")
    assert load_live_stats(connection).average_cost_brl == pytest.approx(0.002)
    connection.execute("UPDATE attendances SET cost_brl = NULL WHERE id = 1")
    assert load_live_stats(connection).average_cost_brl is None


def test_every_action_and_reason_has_a_portuguese_label() -> None:
    live = load_texts(UI_TEXTS)["dashboard"]["live"]
    assert {action.value for action in Action} <= set(live["actions"])
    assert {reason.value for reason in HandoffReason} <= set(live["reasons"])


def test_kpis_are_built_for_populated_stats(connection: sqlite3.Connection) -> None:
    populate(connection)
    stats = load_live_stats(connection)
    primary = {kpi.key: kpi for kpi in primary_kpis(stats)}
    assert primary["total"].display == "4"
    assert primary["emergencies"].display == "1"
    assert primary["auto_resolution"].label == "Resolvidos automaticamente"
    assert len(secondary_kpis(stats)) == 2


def test_message_text_is_escaped_in_the_recent_table(connection: sqlite3.Connection) -> None:
    classifier = ScriptedClassifier(make_triage())
    run_triage(connection, "<script>alert(1)</script> sem luz", classifier=classifier)
    html = recent_table_html(load_live_stats(connection).recent)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_bars_show_counts_and_fall_back_to_a_note() -> None:
    html = bars_html({"handoff": 3, "emergency": 1}, {"handoff": "Encaminhado"}, "vazio")
    assert "Encaminhado" in html
    assert "emergency" in html
    assert "vazio" in bars_html({}, {}, "vazio")


def dashboard_with_database(monkeypatch: pytest.MonkeyPatch, path: Path) -> AppTest:
    monkeypatch.setenv("DATABASE_PATH", str(path))
    monkeypatch.setenv("LLM_MODE", "mock")
    return AppTest.from_file(str(ROOT / "ui" / "dashboard.py"), default_timeout=30)


def test_dashboard_live_tab_is_empty_before_any_chat(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    app = dashboard_with_database(monkeypatch, tmp_path / "empty.db").run()
    assert not app.exception
    assert len(app.tabs) == 2
    assert "Nenhum atendimento registrado ainda" in app.tabs[1].markdown[-1].value


def test_dashboard_live_tab_shows_attendances(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "live.db"
    connection = connect(str(database_path))
    initialize(connection)
    populate(connection)
    connection.close()
    app = dashboard_with_database(monkeypatch, database_path).run()
    assert not app.exception
    text = " ".join(element.value for element in app.tabs[1].markdown)
    assert "Resolvidos automaticamente" in text
    assert "sem luz na pituba" in text
    assert "Ocorrência conhecida" in text
