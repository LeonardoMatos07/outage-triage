from dataclasses import replace
from datetime import datetime
from html import escape

from app.texts import load_texts
from eval.live_stats import LiveStats, RecentAttendance
from ui.chat_view import strip_html
from ui.dashboard_view import Kpi, format_decimal, rate_kpi
from ui.view import UI_TEXTS

TIME_FORMAT = "%d/%m %H:%M:%S"


def count_kpi(key: str, count: int, detail: str) -> Kpi:
    labels = load_texts(UI_TEXTS)["dashboard"]["live"]["kpis"]
    return Kpi(
        key=key,
        label=labels[key],
        display=str(count),
        detail=detail,
        ratio=None,
        target=None,
        status="no_target",
    )


def value_kpi_live(key: str, display: str, detail: str, available: bool) -> Kpi:
    labels = load_texts(UI_TEXTS)["dashboard"]["live"]["kpis"]
    return Kpi(
        key=key,
        label=labels[key],
        display=display,
        detail=detail,
        ratio=None,
        target=None,
        status="no_target" if available else "unavailable",
    )


def primary_kpis(stats: LiveStats) -> list[Kpi]:
    details = load_texts(UI_TEXTS)["dashboard"]["live"]["details"]
    labels = load_texts(UI_TEXTS)["dashboard"]["live"]["kpis"]
    share = details["share"]
    automatic = rate_kpi("auto_resolution", stats.auto_resolution, {})
    return [
        count_kpi("total", stats.total, details["total"]),
        replace(automatic, label=labels["automatic"]),
        count_kpi(
            "emergencies",
            stats.emergencies,
            share.format(count=stats.emergencies, total=stats.total),
        ),
        count_kpi(
            "handed",
            stats.handed_to_human,
            share.format(count=stats.handed_to_human, total=stats.total),
        ),
    ]


def secondary_kpis(stats: LiveStats) -> list[Kpi]:
    details = load_texts(UI_TEXTS)["dashboard"]["live"]["details"]
    cost = stats.average_cost_brl
    median = stats.latency.median_seconds
    return [
        value_kpi_live(
            "cost",
            "R$ " + format_decimal(cost, 6) if cost is not None else format_decimal(cost, 6),
            details["cost_unavailable"] if cost is None else "",
            cost is not None,
        ),
        value_kpi_live(
            "latency",
            format_decimal(median, 2) + " s" if median is not None else format_decimal(median, 2),
            details["latency"].format(p95=format_decimal(stats.latency.p95_seconds, 2)),
            median is not None,
        ),
    ]


def bars_html(counts: dict[str, int], labels: dict[str, str], empty_text: str) -> str:
    if not counts:
        return strip_html("notice", "ⓘ", "", empty_text)
    maximum = max(counts.values())
    rows = "".join(
        '<div class="dx-bar-row">'
        f'<div class="dx-bar-row__label">{escape(labels.get(key, key))}</div>'
        '<div class="dx-meter" aria-hidden="true">'
        f'<div class="dx-meter__fill" style="width:{count / maximum * 100:.1f}%;'
        '--dx-tone:var(--dx-info)"></div></div>'
        f'<div class="dx-bar-row__count">{count}</div></div>'
        for key, count in counts.items()
    )
    return f'<div class="dx-bars">{rows}</div>'


def format_time(created_at: str) -> str:
    return datetime.fromisoformat(created_at).strftime(TIME_FORMAT)


def recent_row_html(entry: RecentAttendance) -> str:
    live = load_texts(UI_TEXTS)["dashboard"]["live"]
    action = live["actions"].get(entry.action, entry.action)
    reason = (
        live["reasons"].get(entry.handoff_reason, entry.handoff_reason)
        if entry.handoff_reason
        else live["no_reason"]
    )
    return (
        f'<tr><td class="dx-num">{escape(format_time(entry.created_at))}</td>'
        f"<td>{escape(entry.message)}</td><td>{escape(action)}</td>"
        f"<td>{escape(reason)}</td><td><code>{escape(entry.model)}</code></td></tr>"
    )


def recent_table_html(recent: list[RecentAttendance]) -> str:
    columns = load_texts(UI_TEXTS)["dashboard"]["live"]["columns"]
    head = "".join(
        f'<th scope="col">{escape(columns[key])}</th>'
        for key in ("time", "message", "action", "reason", "model")
    )
    rows = "".join(recent_row_html(entry) for entry in recent)
    return (
        '<div class="dx-table-wrap"><table class="dx-table">'
        f"<thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>"
    )


def live_empty_html() -> str:
    live = load_texts(UI_TEXTS)["dashboard"]["live"]
    return (
        '<div class="dx-empty">'
        f'<div class="dx-empty__title">{escape(live["empty_title"])}</div>'
        f'<div class="dx-empty__hint">{escape(live["empty_hint"])}</div></div>'
    )
