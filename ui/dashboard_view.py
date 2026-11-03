import math
from dataclasses import dataclass
from html import escape

from app.texts import load_texts
from eval.metrics import ErrorCase, EvalMetrics, Rate, TargetResult
from eval.report import REPORT_TEXTS, EvalReport
from ui.chat_view import strip_html
from ui.view import UI_TEXTS

CONFUSION_LEVELS = 5
INTENT_ORDER = ("outage", "billing", "reconnection", "other", "none")
STATUS_ICONS = {"met": "✓", "missed": "✕", "no_target": "◦", "unavailable": "–"}
STATUS_TONES = {
    "met": "good",
    "missed": "critical",
    "no_target": "neutral",
    "unavailable": "neutral",
}
CARD_TONES = {"met": "met", "missed": "missed", "no_target": "none", "unavailable": "none"}
METER_FILLS = {"met": "var(--dx-good)", "missed": "var(--dx-critical)"}


@dataclass(frozen=True)
class Kpi:
    key: str
    label: str
    display: str
    detail: str
    ratio: float | None
    target: float | None
    status: str


def decimal_comma(text: str) -> str:
    return text.replace(".", ",")


def format_percent(value: float | None) -> str:
    unavailable = load_texts(REPORT_TEXTS)["not_available"]
    return unavailable if value is None else decimal_comma(f"{value:.1%}")


def format_decimal(value: float | None, decimals: int) -> str:
    unavailable = load_texts(REPORT_TEXTS)["not_available"]
    return unavailable if value is None else decimal_comma(f"{value:.{decimals}f}")


def kpi_status(ratio: float | None, target: TargetResult | None) -> str:
    if ratio is None:
        return "unavailable"
    if target is None:
        return "no_target"
    return "met" if target.met else "missed"


def rate_kpi(key: str, rate: Rate, targets: dict[str, TargetResult]) -> Kpi:
    dashboard = load_texts(UI_TEXTS)["dashboard"]
    target = targets.get(key)
    return Kpi(
        key=key,
        label=load_texts(REPORT_TEXTS)["metric_names"][key],
        display=format_percent(rate.value),
        detail=dashboard["fraction"].format(correct=rate.correct, total=rate.total),
        ratio=rate.value,
        target=target.target if target else None,
        status=kpi_status(rate.value, target),
    )


def value_kpi(key: str, value: float | None, display: str, detail: str) -> Kpi:
    return Kpi(
        key=key,
        label=load_texts(REPORT_TEXTS)["metric_names"][key],
        display=display,
        detail=detail,
        ratio=None,
        target=None,
        status="unavailable" if value is None else "no_target",
    )


def target_map(report: EvalReport) -> dict[str, TargetResult]:
    return {target.name: target for target in report.targets}


def safety_kpis(report: EvalReport) -> dict[str, Kpi]:
    metrics = report.metrics
    targets = target_map(report)
    return {
        "emergency_recall": rate_kpi("emergency_recall", metrics.emergency.recall, targets),
        "injection_resistance": rate_kpi(
            "injection_resistance", metrics.injection_resistance, targets
        ),
        "emergency_precision": rate_kpi(
            "emergency_precision", metrics.emergency.precision, targets
        ),
    }


def quality_kpis(report: EvalReport) -> list[Kpi]:
    metrics = report.metrics
    targets = target_map(report)
    return [
        rate_kpi("intent_accuracy", metrics.intent_accuracy, targets),
        rate_kpi("neighborhood_accuracy", metrics.neighborhood_accuracy, targets),
        rate_kpi("action_accuracy", metrics.action_accuracy, targets),
    ]


def operation_kpis(report: EvalReport) -> list[Kpi]:
    metrics = report.metrics
    dashboard = load_texts(UI_TEXTS)["dashboard"]
    cost = metrics.cost_per_message_brl
    cost_display = format_decimal(cost, 6)
    return [
        rate_kpi("auto_resolution", metrics.auto_resolution, {}),
        value_kpi(
            "cost_per_message",
            cost,
            cost_display if cost is None else f"R$ {cost_display}",
            dashboard["cost_detail"],
        ),
        value_kpi(
            "latency_median",
            metrics.latency.median_seconds,
            format_decimal(metrics.latency.median_seconds, 2) + " s",
            dashboard["latency_detail"].format(p95=format_decimal(metrics.latency.p95_seconds, 2)),
        ),
    ]


def status_badge_html(status: str) -> str:
    label = load_texts(UI_TEXTS)["dashboard"]["status"][status]
    return (
        f'<span class="dx-badge dx-badge--{STATUS_TONES[status]}">'
        f'<span aria-hidden="true">{STATUS_ICONS[status]}</span>{escape(label)}</span>'
    )


def meter_html(kpi: Kpi) -> str:
    if kpi.ratio is None:
        return ""
    fill = METER_FILLS.get(kpi.status, "var(--dx-info)")
    width = max(0.0, min(1.0, kpi.ratio)) * 100
    target_tick = (
        f'<div class="dx-meter__target" style="left:{kpi.target * 100:.1f}%"></div>'
        if kpi.target is not None
        else ""
    )
    return (
        '<div class="dx-meter" aria-hidden="true">'
        f'<div class="dx-meter__fill" style="width:{width:.1f}%;--dx-tone:{fill}"></div>'
        f"{target_tick}</div>"
    )


def kpi_card_html(kpi: Kpi, hero: bool = False) -> str:
    dashboard = load_texts(UI_TEXTS)["dashboard"]
    hero_class = " dx-card--hero" if hero else ""
    target_line = (
        f'<div class="dx-card__detail">{escape(dashboard["target"])}: '
        f"{format_percent(kpi.target)}</div>"
        if kpi.target is not None
        else ""
    )
    return (
        f'<div class="dx-card dx-card--{CARD_TONES[kpi.status]}{hero_class}">'
        f'<div class="dx-card__label">{escape(kpi.label)}</div>'
        f'<div class="dx-card__value">{escape(kpi.display)}</div>'
        f"{meter_html(kpi)}"
        f'<div class="dx-card__detail">{escape(kpi.detail)}</div>'
        f"{target_line}"
        f'<div class="dx-card__status">{status_badge_html(kpi.status)}</div></div>'
    )


def run_summary_html(report: EvalReport) -> str:
    meta = load_texts(UI_TEXTS)["dashboard"]["meta"]
    items = [
        (meta["model"], report.model),
        (meta["split"], report.split),
        (meta["generated_at"], report.generated_at),
        (meta["examples_used"], str(report.examples_used)),
        (meta["ignored"], str(report.ignored_unreviewed)),
    ]
    chips = "".join(
        f'<span class="dx-chip"><b>{escape(label)}</b>{escape(value)}</span>'
        for label, value in items
    )
    return f'<div class="dx-chips">{chips}</div>'


def title_html() -> str:
    dashboard = load_texts(UI_TEXTS)["dashboard"]
    return (
        f'<h1 class="dx-title">{escape(dashboard["title"])}</h1>'
        f'<div class="dx-sub">{escape(dashboard["subtitle"])}</div>'
    )


def section_html(title: str, badge: str = "") -> str:
    return f'<h2 class="dx-h2">{escape(title)}{badge}</h2>'


def safety_alert_html(report: EvalReport) -> str:
    safety = load_texts(UI_TEXTS)["dashboard"]["safety"]
    recall = report.metrics.emergency.recall
    missed = recall.total - recall.correct
    false_alarms = (
        report.metrics.emergency.precision.total - report.metrics.emergency.precision.correct
    )
    if missed > 0:
        return strip_html("critical", "✕", "", safety["alert"].format(count=missed))
    text = safety["ok"]
    if false_alarms > 0:
        text = f"{text} {safety['false_alarms'].format(count=false_alarms)}"
    return strip_html("good", "✓", "", text)


def error_count_badge(count: int) -> str:
    tone = "critical" if count else "good"
    icon = "✕" if count else "✓"
    return (
        f'<span class="dx-badge dx-badge--{tone}">'
        f'<span aria-hidden="true">{icon}</span>{count}</span>'
    )


def errors_table_html(errors: list[ErrorCase]) -> str:
    dashboard = load_texts(UI_TEXTS)["dashboard"]
    if not errors:
        return strip_html("good", "✓", "", dashboard["safety"]["none_found"])
    columns = dashboard["columns"]
    head = "".join(
        f'<th scope="col">{escape(columns[key])}</th>'
        for key in ("id", "message", "expected", "predicted")
    )
    rows = "".join(
        f'<tr><td class="dx-num">{escape(error.id)}</td><td>{escape(error.message)}</td>'
        f"<td><code>{escape(error.expected)}</code></td>"
        f"<td><code>{escape(error.predicted)}</code></td></tr>"
        for error in errors
    )
    return (
        '<div class="dx-table-wrap"><table class="dx-table">'
        f"<thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>"
    )


def ordered_labels(matrix: dict[str, dict[str, int]]) -> tuple[list[str], list[str]]:
    expected = set(matrix)
    predicted = {label for row in matrix.values() for label in row}
    everything = expected | predicted
    ordered = [label for label in INTENT_ORDER if label in everything]
    ordered += sorted(everything - set(INTENT_ORDER))
    return [label for label in ordered if label in expected], [
        label for label in ordered if label in predicted
    ]


def confusion_cell_class(count: int, maximum: int, correct: bool) -> str:
    if count == 0:
        return "dx-cell--zero"
    level = max(1, min(CONFUSION_LEVELS, math.ceil(count / maximum * CONFUSION_LEVELS)))
    return f"dx-cell--{'ok' if correct else 'err'}-{level}"


def confusion_html(matrix: dict[str, dict[str, int]]) -> str:
    confusion = load_texts(UI_TEXTS)["dashboard"]["confusion"]
    row_labels, column_labels = ordered_labels(matrix)
    maximum = max((count for row in matrix.values() for count in row.values()), default=1)
    header = "".join(f'<th scope="col">{escape(label)}</th>' for label in column_labels)
    body = ""
    for expected in row_labels:
        cells = ""
        for predicted in column_labels:
            count = matrix[expected].get(predicted, 0)
            css = confusion_cell_class(count, maximum, expected == predicted)
            cells += f'<td class="{css}">{count}</td>'
        body += f'<tr><th scope="row" class="dx-cm__row">{escape(expected)}</th>{cells}</tr>'
    return (
        '<div class="dx-table-wrap" style="padding:0.5rem;display:inline-block;max-width:100%">'
        '<table class="dx-cm">'
        f'<thead><tr><th></th><th colspan="{len(column_labels)}">'
        f"{escape(confusion['predicted'])} →</th></tr>"
        f'<tr><th class="dx-cm__row">{escape(confusion["expected"])} ↓</th>{header}</tr></thead>'
        f"<tbody>{body}</tbody></table></div>"
    )


def confusion_legend_html() -> str:
    confusion = load_texts(UI_TEXTS)["dashboard"]["confusion"]
    return (
        '<div class="dx-legend">'
        f'<span><span class="dx-swatch" style="background:#3987e5"></span>'
        f"{escape(confusion['legend_ok'])}</span>"
        f'<span><span class="dx-swatch" style="background:#eb6834"></span>'
        f"{escape(confusion['legend_error'])}</span>"
        f"<span>{escape(confusion['legend_scale'])}</span></div>"
    )


HIGHER_IS_BETTER = (
    "action_accuracy",
    "intent_accuracy",
    "emergency_recall",
    "injection_resistance",
)
LOWER_IS_BETTER = ("cost_per_message", "latency_median")
COMPARISON_KEYS = (*HIGHER_IS_BETTER, "auto_resolution", *LOWER_IS_BETTER)


def comparison_values(metrics: EvalMetrics) -> dict[str, float | None]:
    return {
        "action_accuracy": metrics.action_accuracy.value,
        "intent_accuracy": metrics.intent_accuracy.value,
        "emergency_recall": metrics.emergency.recall.value,
        "injection_resistance": metrics.injection_resistance.value,
        "auto_resolution": metrics.auto_resolution.value,
        "cost_per_message": metrics.cost_per_message_brl,
        "latency_median": metrics.latency.median_seconds,
    }


def winners(values: dict[str, float], lower_is_better: bool) -> set[str]:
    best = min(values.values()) if lower_is_better else max(values.values())
    return {model for model, value in values.items() if value == best}


def best_models(reports: list[EvalReport]) -> dict[str, set[str]]:
    rows = {report.model: comparison_values(report.metrics) for report in reports}
    best: dict[str, set[str]] = {}
    for key in (*HIGHER_IS_BETTER, *LOWER_IS_BETTER):
        known = {model: row[key] for model, row in rows.items() if row[key] is not None}
        if known:
            best[key] = winners(
                {m: v for m, v in known.items() if v is not None}, key in LOWER_IS_BETTER
            )
    return best


def comparison_cells(report: EvalReport) -> dict[str, str]:
    values = comparison_values(report.metrics)
    return {
        key: format_decimal(value, 6 if key == "cost_per_message" else 2)
        if key in LOWER_IS_BETTER
        else format_percent(value)
        for key, value in values.items()
    }


def comparison_html(reports: list[EvalReport]) -> str:
    names = load_texts(REPORT_TEXTS)["metric_names"]
    comparison = load_texts(REPORT_TEXTS)["comparison"]
    dashboard = load_texts(UI_TEXTS)["dashboard"]
    best = best_models(reports)
    keys = list(COMPARISON_KEYS)
    head = f'<th scope="col">{escape(comparison["model"])}</th>' + "".join(
        f'<th scope="col">{escape(names[key])}</th>' for key in keys
    )
    rows = ""
    for report in reports:
        cells = comparison_cells(report)
        row = f"<td><code>{escape(report.model)}</code></td>"
        for key in keys:
            is_best = report.model in best.get(key, set())
            css = "dx-num dx-best" if is_best else "dx-num"
            marker = "★ " if is_best else ""
            row += f'<td class="{css}">{marker}{escape(cells[key])}</td>'
        rows += f"<tr>{row}</tr>"
    return (
        '<div class="dx-table-wrap"><table class="dx-table">'
        f"<thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>"
        f'<div class="dx-legend"><span>{escape(dashboard["best_legend"])}</span></div>'
    )


def empty_state_html(mock_mode: bool) -> str:
    empty = load_texts(UI_TEXTS)["dashboard"]["empty"]
    command = empty["mock_command"] if mock_mode else empty["command"]
    hint = empty["mock_hint"] if mock_mode else empty["hint"]
    return (
        '<div class="dx-empty">'
        f'<div class="dx-empty__title">{escape(empty["title"])}</div>'
        f'<div class="dx-empty__hint">{escape(hint)}</div>'
        f"<code>{escape(command)}</code></div>"
    )
