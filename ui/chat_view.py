from html import escape

from app.texts import load_texts
from ui.view import UI_TEXTS, OutcomeKind

OUTCOME_ICONS = {
    OutcomeKind.EMERGENCY: "⚠",
    OutcomeKind.QUESTION: "?",
    OutcomeKind.HANDOFF: "↗",
    OutcomeKind.AUTOMATIC: "✓",
}


def header_html() -> str:
    brand = load_texts(UI_TEXTS)["brand"]
    chat = load_texts(UI_TEXTS)["chat"]
    return (
        '<div class="dx-header">'
        f'<div class="dx-mark" aria-hidden="true">{escape(brand["monogram"])}</div>'
        "<div>"
        f'<div class="dx-brand">{escape(brand["name"])}'
        f'<span class="dx-tag">{escape(brand["tag"])}</span></div>'
        f'<div class="dx-sub">{escape(chat["title"])}. {escape(chat["subtitle"])}</div>'
        "</div></div>"
    )


def strip_html(tone: str, icon: str, label: str, text: str) -> str:
    lead = f"<strong>{escape(label)}</strong> " if label else ""
    return (
        f'<div class="dx-strip dx-strip--{tone}" role="note">'
        f'<span class="dx-strip__icon" aria-hidden="true">{escape(icon)}</span>'
        f"<div>{lead}{escape(text)}</div></div>"
    )


def notice_html() -> str:
    ui = load_texts(UI_TEXTS)
    return strip_html("notice", "ⓘ", ui["notice_label"], ui["notice"])


def mock_banner_html() -> str:
    ui = load_texts(UI_TEXTS)
    return strip_html("mock", "◆", ui["mock_label"], ui["mock_text"])


def badge_html(kind: OutcomeKind, label: str) -> str:
    return (
        f'<span class="dx-badge dx-badge--{kind.value}">'
        f'<span aria-hidden="true">{OUTCOME_ICONS[kind]}</span>{escape(label)}</span>'
    )


def protocol_html(protocol: str) -> str:
    label = load_texts(UI_TEXTS)["chat"]["protocol_label"]
    return (
        '<div class="dx-protocol">'
        f'<span class="dx-protocol__label">{escape(label)}</span>'
        f'<span class="dx-protocol__code">{escape(protocol)}</span></div>'
    )


def reply_html(
    reply: str, kind: OutcomeKind | None, label: str | None, protocol: str | None
) -> str:
    modifier = f" dx-reply--{kind.value}" if kind else ""
    badge = (
        f'<div class="dx-reply__badge">{badge_html(kind, label)}</div>' if kind and label else ""
    )
    protocol_block = protocol_html(protocol) if protocol else ""
    return (
        f'<div class="dx-reply{modifier}">{badge}'
        f'<p class="dx-reply__text">{escape(reply)}</p>{protocol_block}</div>'
    )


def details_html(details: dict[str, str]) -> str:
    rows = "".join(
        f"<dt>{escape(name)}</dt><dd><code>{escape(value)}</code></dd>"
        for name, value in details.items()
    )
    return f'<dl class="dx-kv">{rows}</dl>'


def label_html(text: str) -> str:
    return f'<div class="dx-label">{escape(text)}</div>'
