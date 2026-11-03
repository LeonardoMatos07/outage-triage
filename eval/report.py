import re
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from app.settings import ROOT
from app.texts import load_texts
from eval.metrics import (
    ErrorCase,
    EvalMetrics,
    Rate,
    TargetResult,
    evaluate_targets,
)

REPORTS_DIR = ROOT / "reports"
REPORT_TEXTS = "report_pt.yaml"


class EvalReport(BaseModel):
    model: str
    split: str
    generated_at: str
    examples_used: int
    ignored_unreviewed: int
    metrics: EvalMetrics
    targets: list[TargetResult]
    emergency_errors: list[ErrorCase]
    injection_errors: list[ErrorCase]


def build_report(
    model: str,
    split: str,
    examples_used: int,
    ignored_unreviewed: int,
    metrics: EvalMetrics,
    emergency_errors: list[ErrorCase],
    injection_errors: list[ErrorCase],
) -> EvalReport:
    return EvalReport(
        model=model,
        split=split,
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        examples_used=examples_used,
        ignored_unreviewed=ignored_unreviewed,
        metrics=metrics,
        targets=evaluate_targets(metrics),
        emergency_errors=emergency_errors,
        injection_errors=injection_errors,
    )


def report_date(report: EvalReport) -> str:
    return report.generated_at[:10]


def report_stem(report: EvalReport) -> str:
    safe_model = re.sub(r"[^A-Za-z0-9._-]", "_", report.model)
    return f"eval-{report_date(report)}-{report.split}-{safe_model}"


def format_rate(rate: Rate) -> str:
    texts = load_texts(REPORT_TEXTS)
    if rate.value is None:
        return str(texts["not_available"])
    return f"{rate.value:.1%} ({rate.correct}/{rate.total})"


def format_number(value: float | None, decimals: int) -> str:
    if value is None:
        return str(load_texts(REPORT_TEXTS)["not_available"])
    return f"{value:.{decimals}f}"


def markdown_table(header: list[str], rows: list[list[str]]) -> list[str]:
    escaped = [[cell.replace("|", "\\|").replace("\n", " ") for cell in row] for row in rows]
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(row) + " |" for row in escaped]
    return lines


def metric_rows(report: EvalReport) -> list[list[str]]:
    texts = load_texts(REPORT_TEXTS)
    names = texts["metric_names"]
    metrics = report.metrics
    targets = {target.name: target for target in report.targets}

    def with_target(key: str, rate: Rate) -> list[str]:
        target = targets.get(key)
        if target is None:
            return [names[key], format_rate(rate), "", ""]
        verdict = texts["affirmative"] if target.met else texts["negative"]
        return [names[key], format_rate(rate), f"{target.target:.0%}", verdict]

    return [
        with_target("intent_accuracy", metrics.intent_accuracy),
        with_target("emergency_recall", metrics.emergency.recall),
        with_target("emergency_precision", metrics.emergency.precision),
        with_target("emergency_keyword_only_recall", metrics.emergency.keyword_only_recall),
        with_target("emergency_llm_only_recall", metrics.emergency.llm_only_recall),
        with_target("neighborhood_accuracy", metrics.neighborhood_accuracy),
        with_target("action_accuracy", metrics.action_accuracy),
        with_target("auto_resolution", metrics.auto_resolution),
        with_target("injection_resistance", metrics.injection_resistance),
        [names["cost_per_message"], format_number(metrics.cost_per_message_brl, 6), "", ""],
        [names["latency_median"], format_number(metrics.latency.median_seconds, 2), "", ""],
        [names["latency_p95"], format_number(metrics.latency.p95_seconds, 2), "", ""],
    ]


def confusion_lines(report: EvalReport) -> list[str]:
    texts = load_texts(REPORT_TEXTS)
    matrix = report.metrics.intent_confusion
    predicted_labels = sorted({label for row in matrix.values() for label in row})
    rows = [
        [expected] + [str(matrix[expected].get(label, 0)) for label in predicted_labels]
        for expected in sorted(matrix)
    ]
    return markdown_table([texts["confusion_expected"], *predicted_labels], rows)


def error_lines(errors: list[ErrorCase]) -> list[str]:
    texts = load_texts(REPORT_TEXTS)
    if not errors:
        return [str(texts["none_found"])]
    columns = texts["error_columns"]
    rows = [[error.id, error.message, error.expected, error.predicted] for error in errors]
    return markdown_table(
        [columns["id"], columns["message"], columns["expected"], columns["predicted"]], rows
    )


def render_report(report: EvalReport) -> str:
    texts = load_texts(REPORT_TEXTS)
    run = texts["run"]
    columns = texts["columns"]
    lines = [
        f"# {texts['title']}",
        "",
        f"> {texts['notice']}",
        "",
        f"- {run['model']}: `{report.model}`",
        f"- {run['split']}: `{report.split}`",
        f"- {run['generated_at']}: {report.generated_at}",
        f"- {run['examples_used']}: {report.examples_used}",
        f"- {run['ignored']}: {report.ignored_unreviewed}",
        "",
        f"## {texts['metrics_heading']}",
        "",
        str(texts["targets_note"]),
        "",
        *markdown_table(
            [columns["metric"], columns["result"], columns["target"], columns["met"]],
            metric_rows(report),
        ),
        "",
        f"## {texts['confusion_heading']}",
        "",
        *confusion_lines(report),
        "",
        f"## {texts['emergency_errors_heading']}",
        "",
        *error_lines(report.emergency_errors),
        "",
        f"## {texts['injection_errors_heading']}",
        "",
        *error_lines(report.injection_errors),
        "",
    ]
    return "\n".join(lines)


def comparison_rows(reports: list[EvalReport]) -> list[list[str]]:
    return [
        [
            report.model,
            format_rate(report.metrics.action_accuracy),
            format_rate(report.metrics.intent_accuracy),
            format_rate(report.metrics.emergency.recall),
            format_rate(report.metrics.injection_resistance),
            format_rate(report.metrics.auto_resolution),
            format_number(report.metrics.cost_per_message_brl, 6),
            format_number(report.metrics.latency.median_seconds, 2),
        ]
        for report in reports
    ]


def render_comparison(reports: list[EvalReport]) -> str:
    texts = load_texts(REPORT_TEXTS)
    names = texts["metric_names"]
    comparison = texts["comparison"]
    header = [
        comparison["model"],
        names["action_accuracy"],
        names["intent_accuracy"],
        names["emergency_recall"],
        names["injection_resistance"],
        names["auto_resolution"],
        names["cost_per_message"],
        names["latency_median"],
    ]
    lines = [
        f"# {comparison['heading']}",
        "",
        f"> {texts['notice']}",
        "",
        f"- {comparison['split']}: `{reports[0].split}`",
        f"- {texts['run']['generated_at']}: {reports[0].generated_at}",
        "",
        str(comparison["note"]),
        "",
        *markdown_table(header, comparison_rows(reports)),
        "",
    ]
    return "\n".join(lines)


def write_report(report: EvalReport, directory: Path = REPORTS_DIR) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    markdown_path = directory / f"{report_stem(report)}.md"
    json_path = directory / f"{report_stem(report)}.json"
    markdown_path.write_text(render_report(report), encoding="utf-8", newline="\n")
    json_path.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n")
    return markdown_path, json_path


def write_comparison(reports: list[EvalReport], directory: Path = REPORTS_DIR) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"comparison-{report_date(reports[0])}-{reports[0].split}.md"
    path.write_text(render_comparison(reports), encoding="utf-8", newline="\n")
    return path


def load_reports(directory: Path = REPORTS_DIR) -> list[EvalReport]:
    reports = [
        EvalReport.model_validate_json(path.read_text(encoding="utf-8"))
        for path in sorted(directory.glob("eval-*.json"))
    ]
    return sorted(reports, key=lambda report: report.generated_at)


def load_latest_report(directory: Path = REPORTS_DIR) -> EvalReport | None:
    reports = load_reports(directory)
    return reports[-1] if reports else None


def same_run_reports(latest: EvalReport, directory: Path = REPORTS_DIR) -> list[EvalReport]:
    return [
        report
        for report in load_reports(directory)
        if report.split == latest.split and report_date(report) == report_date(latest)
    ]
