from pathlib import Path

import streamlit as st

from app.settings import DEMO_REPORTS_DIR, is_mock_mode
from app.texts import load_texts
from eval.report import REPORT_TEXTS, REPORTS_DIR, EvalReport, load_latest_report, same_run_reports
from ui.chat_view import mock_banner_html, notice_html, strip_html
from ui.dashboard_view import (
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
from ui.theme import inject_theme
from ui.view import UI_TEXTS

TEXTS = load_texts(UI_TEXTS)
DASHBOARD_TEXTS = TEXTS["dashboard"]
REPORT = load_texts(REPORT_TEXTS)
HERO_COLUMN_WEIGHTS = [5, 3, 3]


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


def main() -> None:
    st.set_page_config(
        page_title=DASHBOARD_TEXTS["page_title"], page_icon=TEXTS["page_icon"], layout="wide"
    )
    inject_theme(wide=True)
    st.markdown(title_html(), unsafe_allow_html=True)
    reports_dir = DEMO_REPORTS_DIR if is_mock_mode() else REPORTS_DIR
    render_notices()
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


main()
