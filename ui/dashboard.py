from pathlib import Path

import streamlit as st

from app.database import connect, initialize
from app.settings import DEMO_REPORTS_DIR, database_path, is_mock_mode
from app.texts import load_texts
from eval.live_stats import LiveStats, load_live_stats
from eval.report import REPORT_TEXTS, REPORTS_DIR, EvalReport, load_latest_report, same_run_reports
from ui.chat_view import mock_banner_html, notice_html, strip_html
from ui.dashboard_view import (
    Kpi,
    comparison_html,
    confusion_html,
    confusion_legend_html,
    empty_state_html,
    error_count_badge,
    errors_table_html,
    kpi_card_html,
    operation_kpis,
    quality_kpis,
    run_summary_html,
    safety_alert_html,
    safety_kpis,
    section_html,
    title_html,
)
from ui.live_view import (
    bars_html,
    live_empty_html,
    primary_kpis,
    recent_table_html,
    secondary_kpis,
)
from ui.theme import inject_theme
from ui.view import UI_TEXTS

TEXTS = load_texts(UI_TEXTS)
DASHBOARD_TEXTS = TEXTS["dashboard"]
REPORT = load_texts(REPORT_TEXTS)
HERO_COLUMN_WEIGHTS = [5, 3, 3]
LIVE_REFRESH_SECONDS = 5
LIVE_TEXTS = DASHBOARD_TEXTS["live"]


def render_notices() -> None:
    st.markdown(notice_html(), unsafe_allow_html=True)
    if is_mock_mode():
        st.markdown(mock_banner_html(), unsafe_allow_html=True)
    st.markdown(strip_html("notice", "ⓘ", "", REPORT["targets_note"]), unsafe_allow_html=True)


def render_safety(report: EvalReport) -> None:
    st.markdown(section_html(DASHBOARD_TEXTS["sections"]["safety"]), unsafe_allow_html=True)
    kpis = safety_kpis(report)
    columns = st.columns(HERO_COLUMN_WEIGHTS)
    columns[0].markdown(kpi_card_html(kpis["emergency_recall"], hero=True), unsafe_allow_html=True)
    columns[1].markdown(kpi_card_html(kpis["injection_resistance"]), unsafe_allow_html=True)
    columns[2].markdown(kpi_card_html(kpis["emergency_precision"]), unsafe_allow_html=True)
    st.markdown(safety_alert_html(report), unsafe_allow_html=True)
    safety = DASHBOARD_TEXTS["safety"]
    st.markdown(
        section_html(safety["emergency_errors"], error_count_badge(len(report.emergency_errors))),
        unsafe_allow_html=True,
    )
    st.markdown(errors_table_html(report.emergency_errors), unsafe_allow_html=True)
    st.markdown(
        section_html(safety["injection_errors"], error_count_badge(len(report.injection_errors))),
        unsafe_allow_html=True,
    )
    st.markdown(errors_table_html(report.injection_errors), unsafe_allow_html=True)


def render_kpi_row(title: str, report: EvalReport, quality: bool) -> None:
    st.markdown(section_html(title), unsafe_allow_html=True)
    kpis = quality_kpis(report) if quality else operation_kpis(report)
    for column, kpi in zip(st.columns(len(kpis)), kpis, strict=True):
        column.markdown(kpi_card_html(kpi), unsafe_allow_html=True)


def render_comparison(latest: EvalReport, reports_dir: Path) -> None:
    reports = same_run_reports(latest, reports_dir)
    if len(reports) < 2:
        return
    st.markdown(section_html(DASHBOARD_TEXTS["sections"]["comparison"]), unsafe_allow_html=True)
    st.caption(REPORT["comparison"]["note"])
    st.markdown(comparison_html(reports), unsafe_allow_html=True)


def render_confusion(report: EvalReport) -> None:
    st.markdown(section_html(DASHBOARD_TEXTS["sections"]["confusion"]), unsafe_allow_html=True)
    st.markdown(confusion_html(report.metrics.intent_confusion), unsafe_allow_html=True)
    st.markdown(confusion_legend_html(), unsafe_allow_html=True)


def load_current_stats() -> LiveStats:
    connection = connect(database_path())
    try:
        initialize(connection)
        return load_live_stats(connection)
    finally:
        connection.close()


def render_kpis(kpis: list[Kpi]) -> None:
    for column, kpi in zip(st.columns(len(kpis)), kpis, strict=True):
        column.markdown(kpi_card_html(kpi), unsafe_allow_html=True)


def render_live_details(stats: LiveStats) -> None:
    sections = LIVE_TEXTS["sections"]
    st.markdown(section_html(sections["actions"]), unsafe_allow_html=True)
    st.markdown(
        bars_html(stats.by_action, LIVE_TEXTS["actions"], LIVE_TEXTS["no_handoffs"]),
        unsafe_allow_html=True,
    )
    st.markdown(section_html(sections["reasons"]), unsafe_allow_html=True)
    st.markdown(
        bars_html(stats.by_handoff_reason, LIVE_TEXTS["reasons"], LIVE_TEXTS["no_handoffs"]),
        unsafe_allow_html=True,
    )
    st.markdown(section_html(sections["recent"]), unsafe_allow_html=True)
    st.markdown(recent_table_html(stats.recent), unsafe_allow_html=True)


@st.fragment(run_every=LIVE_REFRESH_SECONDS)
def render_live() -> None:
    st.caption(LIVE_TEXTS["hint"])
    stats = load_current_stats()
    if stats.total == 0:
        st.markdown(live_empty_html(), unsafe_allow_html=True)
        return
    st.markdown(section_html(LIVE_TEXTS["sections"]["summary"]), unsafe_allow_html=True)
    render_kpis(primary_kpis(stats))
    render_kpis(secondary_kpis(stats))
    render_live_details(stats)


def render_evaluation(reports_dir: Path) -> None:
    latest = load_latest_report(reports_dir)
    if latest is None:
        st.markdown(empty_state_html(is_mock_mode()), unsafe_allow_html=True)
        return
    st.markdown(run_summary_html(latest), unsafe_allow_html=True)
    render_safety(latest)
    render_kpi_row(DASHBOARD_TEXTS["sections"]["quality"], latest, quality=True)
    render_kpi_row(DASHBOARD_TEXTS["sections"]["operation"], latest, quality=False)
    render_comparison(latest, reports_dir)
    render_confusion(latest)


def main() -> None:
    st.set_page_config(
        page_title=DASHBOARD_TEXTS["page_title"], page_icon=TEXTS["page_icon"], layout="wide"
    )
    inject_theme(wide=True)
    st.markdown(title_html(), unsafe_allow_html=True)
    reports_dir = DEMO_REPORTS_DIR if is_mock_mode() else REPORTS_DIR
    render_notices()
    tabs = st.tabs([DASHBOARD_TEXTS["tabs"]["evaluation"], DASHBOARD_TEXTS["tabs"]["live"]])
    with tabs[0]:
        render_evaluation(reports_dir)
    with tabs[1]:
        render_live()


main()
