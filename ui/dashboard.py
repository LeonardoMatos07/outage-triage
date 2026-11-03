import streamlit as st

from app.texts import load_texts
from eval.report import (
    REPORT_TEXTS,
    EvalReport,
    comparison_rows,
    load_latest_report,
    metric_rows,
    same_run_reports,
)
from ui.view import UI_TEXTS

TEXTS = load_texts(UI_TEXTS)
DASHBOARD_TEXTS = TEXTS["dashboard"]
REPORT = load_texts(REPORT_TEXTS)


def as_records(header: list[str], rows: list[list[str]]) -> list[dict[str, str]]:
    return [dict(zip(header, row, strict=True)) for row in rows]


def render_metrics(report: EvalReport) -> None:
    columns = REPORT["columns"]
    header = [columns["metric"], columns["result"], columns["target"], columns["met"]]
    st.subheader(REPORT["metrics_heading"])
    st.caption(REPORT["targets_note"])
    st.table(as_records(header, metric_rows(report)))


def render_confusion(report: EvalReport) -> None:
    matrix = report.metrics.intent_confusion
    predicted_labels = sorted({label for row in matrix.values() for label in row})
    header = [REPORT["confusion_expected"], *predicted_labels]
    rows = [
        [expected, *[str(matrix[expected].get(label, 0)) for label in predicted_labels]]
        for expected in sorted(matrix)
    ]
    st.subheader(REPORT["confusion_heading"])
    st.table(as_records(header, rows))


def render_errors(heading: str, errors: list[dict[str, str]]) -> None:
    st.subheader(heading)
    if errors:
        st.table(errors)
    else:
        st.write(REPORT["none_found"])


def error_records(report: EvalReport, injection: bool) -> list[dict[str, str]]:
    columns = REPORT["error_columns"]
    errors = report.injection_errors if injection else report.emergency_errors
    return [
        {
            columns["id"]: error.id,
            columns["message"]: error.message,
            columns["expected"]: error.expected,
            columns["predicted"]: error.predicted,
        }
        for error in errors
    ]


def render_comparison(latest: EvalReport) -> None:
    reports = same_run_reports(latest)
    if len(reports) < 2:
        return
    names = REPORT["metric_names"]
    header = [
        REPORT["comparison"]["model"],
        names["action_accuracy"],
        names["intent_accuracy"],
        names["emergency_recall"],
        names["injection_resistance"],
        names["auto_resolution"],
        names["cost_per_message"],
        names["latency_median"],
    ]
    st.subheader(REPORT["comparison"]["heading"])
    st.caption(REPORT["comparison"]["note"])
    st.table(as_records(header, comparison_rows(reports)))


def main() -> None:
    st.set_page_config(page_title=DASHBOARD_TEXTS["page_title"], layout="wide")
    st.title(DASHBOARD_TEXTS["title"])
    st.warning(TEXTS["notice"])
    latest = load_latest_report()
    if latest is None:
        st.info(DASHBOARD_TEXTS["no_report"])
        return
    run = REPORT["run"]
    st.caption(
        f"{DASHBOARD_TEXTS['latest_report']}: {latest.model} | {run['split']}: {latest.split} | "
        f"{run['generated_at']}: {latest.generated_at} | "
        f"{run['examples_used']}: {latest.examples_used} | "
        f"{run['ignored']}: {latest.ignored_unreviewed}"
    )
    render_metrics(latest)
    render_comparison(latest)
    render_confusion(latest)
    render_errors(REPORT["emergency_errors_heading"], error_records(latest, injection=False))
    render_errors(REPORT["injection_errors_heading"], error_records(latest, injection=True))


main()
