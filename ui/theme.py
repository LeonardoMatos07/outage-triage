import streamlit as st

CHAT_MAX_WIDTH = "50rem"
DASHBOARD_MAX_WIDTH = "78rem"

BASE_CSS = """
:root {
  --dx-good: #0ca30c;
  --dx-critical: #d03b3b;
  --dx-warning: #fab219;
  --dx-info: #2a78d6;
  --dx-mock: #6250d6;
  --dx-line: color-mix(in srgb, currentColor 16%, transparent);
  --dx-soft: color-mix(in srgb, currentColor 5%, transparent);
  --dx-muted: color-mix(in srgb, currentColor 72%, transparent);
}
.block-container {
  max-width: __MAX_WIDTH__;
  padding-top: 2.2rem;
  padding-bottom: 5rem;
}
.dx-header {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  padding: 0.2rem 0 0.4rem;
}
.dx-mark {
  flex: none;
  width: 2.9rem;
  height: 2.9rem;
  border-radius: 0.85rem;
  background: #256abf;
  color: #ffffff;
  display: grid;
  place-items: center;
  font-weight: 700;
  letter-spacing: 0.03em;
}
.dx-brand {
  font-weight: 700;
  font-size: 1.2rem;
  line-height: 1.25;
}
.dx-sub {
  color: var(--dx-muted);
  font-size: 0.92rem;
  line-height: 1.35;
}
.dx-tag {
  font-size: 0.72rem;
  font-weight: 500;
  border: 1px solid var(--dx-line);
  border-radius: 999px;
  padding: 0.05rem 0.55rem;
  margin-left: 0.5rem;
  color: var(--dx-muted);
  vertical-align: middle;
  white-space: nowrap;
}
.dx-strip {
  display: flex;
  gap: 0.6rem;
  align-items: flex-start;
  border: 1px solid var(--dx-line);
  border-left: 4px solid var(--dx-accent);
  background: var(--dx-soft);
  border-radius: 0.65rem;
  padding: 0.55rem 0.8rem;
  font-size: 0.86rem;
  line-height: 1.45;
  margin: 0.35rem 0;
}
.dx-strip--notice { --dx-accent: var(--dx-info); }
.dx-strip--mock { --dx-accent: var(--dx-mock); }
.dx-strip--critical { --dx-accent: var(--dx-critical); }
.dx-strip--good { --dx-accent: var(--dx-good); }
.dx-strip__icon {
  flex: none;
  font-weight: 700;
  color: var(--dx-accent);
}
.dx-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.78rem;
  font-weight: 600;
  line-height: 1.2;
  border-radius: 999px;
  padding: 0.18rem 0.65rem;
  border: 1px solid var(--dx-tone);
  background: color-mix(in srgb, var(--dx-tone) 16%, transparent);
}
.dx-badge--emergency {
  --dx-tone: var(--dx-critical);
  background: var(--dx-critical);
  color: #ffffff;
}
.dx-badge--handoff { --dx-tone: var(--dx-warning); }
.dx-badge--automatic, .dx-badge--good { --dx-tone: var(--dx-good); }
.dx-badge--question, .dx-badge--info { --dx-tone: var(--dx-info); }
.dx-badge--critical { --dx-tone: var(--dx-critical); }
.dx-badge--neutral { --dx-tone: currentColor; }
.dx-reply {
  border: 1px solid var(--dx-line);
  border-left: 4px solid var(--dx-tone, var(--dx-line));
  border-radius: 0.85rem;
  padding: 0.75rem 1rem 0.85rem;
  background: var(--dx-soft);
  line-height: 1.55;
}
.dx-reply__badge { margin-bottom: 0.5rem; }
.dx-reply__text { margin: 0; }
.dx-reply--emergency {
  --dx-tone: var(--dx-critical);
  border-left-width: 7px;
  background: color-mix(in srgb, var(--dx-critical) 11%, transparent);
  border-color: var(--dx-critical);
}
.dx-reply--emergency .dx-reply__text { font-weight: 600; }
.dx-reply--handoff { --dx-tone: var(--dx-warning); }
.dx-reply--automatic { --dx-tone: var(--dx-good); }
.dx-reply--question { --dx-tone: var(--dx-info); }
.dx-protocol {
  display: inline-flex;
  align-items: baseline;
  gap: 0.55rem;
  margin-top: 0.7rem;
  padding: 0.35rem 0.75rem;
  border-radius: 0.6rem;
  border: 1px dashed var(--dx-line);
  background: var(--dx-soft);
}
.dx-protocol__label {
  font-size: 0.72rem;
  color: var(--dx-muted);
  text-transform: uppercase;
  letter-spacing: 0.07em;
}
.dx-protocol__code {
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 1.2rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}
.dx-kv {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 0.35rem 1.1rem;
  margin: 0;
  font-size: 0.88rem;
}
.dx-kv dt { color: var(--dx-muted); }
.dx-kv dd { margin: 0; }
.dx-kv code { font-size: 0.85rem; }
.st-key-examples button {
  border-radius: 999px;
  font-size: 0.86rem;
  padding: 0.2rem 0.85rem;
}
.dx-label {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--dx-muted);
  margin: 0.4rem 0 0.2rem;
}
.dx-h2 {
  font-size: 1.15rem;
  font-weight: 700;
  margin: 1.6rem 0 0.6rem;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
}
.dx-title {
  font-size: 1.9rem;
  font-weight: 700;
  line-height: 1.2;
  margin: 0;
}
.dx-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin: 0.7rem 0 0.2rem;
}
.dx-chip {
  font-size: 0.82rem;
  border: 1px solid var(--dx-line);
  border-radius: 999px;
  padding: 0.12rem 0.7rem;
  background: var(--dx-soft);
  white-space: nowrap;
}
.dx-chip b { color: var(--dx-muted); font-weight: 600; margin-right: 0.3rem; }
.dx-card {
  border: 1px solid var(--dx-line);
  border-top: 4px solid var(--dx-tone, var(--dx-line));
  border-radius: 0.9rem;
  padding: 0.85rem 1rem 1rem;
  background: var(--dx-soft);
  height: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.dx-card--met { --dx-tone: var(--dx-good); }
.dx-card--missed {
  --dx-tone: var(--dx-critical);
  background: color-mix(in srgb, var(--dx-critical) 9%, transparent);
}
.dx-card--none { --dx-tone: var(--dx-info); }
.dx-card__label { font-size: 0.84rem; font-weight: 600; color: var(--dx-muted); }
.dx-card__value { font-size: 2.1rem; font-weight: 700; line-height: 1.1; }
.dx-card--hero .dx-card__value { font-size: 3.4rem; }
.dx-card__detail { font-size: 0.82rem; color: var(--dx-muted); }
.dx-card__status { margin-top: auto; padding-top: 0.2rem; }
.dx-meter {
  position: relative;
  height: 0.5rem;
  border-radius: 999px;
  background: var(--dx-line);
  margin: 0.25rem 0 0.15rem;
}
.dx-meter__fill {
  height: 100%;
  border-radius: 999px;
  background: var(--dx-tone);
}
.dx-meter__target {
  position: absolute;
  top: -3px;
  bottom: -3px;
  width: 2px;
  background: currentColor;
}
.dx-table-wrap {
  overflow-x: auto;
  border: 1px solid var(--dx-line);
  border-radius: 0.75rem;
}
.dx-table {
  border-collapse: collapse;
  width: 100%;
  font-size: 0.88rem;
}
.dx-table th {
  text-align: left;
  font-weight: 600;
  color: var(--dx-muted);
  padding: 0.55rem 0.75rem;
  border-bottom: 1px solid var(--dx-line);
  white-space: nowrap;
}
.dx-table td {
  padding: 0.55rem 0.75rem;
  border-bottom: 1px solid var(--dx-line);
  vertical-align: top;
}
.dx-table tr:last-child td { border-bottom: 0; }
.dx-table code { font-size: 0.82rem; }
.dx-num { font-variant-numeric: tabular-nums; white-space: nowrap; }
.dx-best {
  font-weight: 700;
  background: color-mix(in srgb, var(--dx-info) 16%, transparent);
}
.dx-cm {
  border-collapse: separate;
  border-spacing: 3px;
  font-size: 0.88rem;
}
.dx-cm th {
  font-weight: 600;
  color: var(--dx-muted);
  padding: 0.3rem 0.6rem;
  text-align: center;
}
.dx-cm th.dx-cm__row { text-align: right; white-space: nowrap; }
.dx-cm td {
  min-width: 3.4rem;
  height: 2.7rem;
  text-align: center;
  font-weight: 600;
  border-radius: 0.4rem;
  font-variant-numeric: tabular-nums;
}
.dx-cell--zero { color: var(--dx-muted); background: var(--dx-soft); font-weight: 400; }
.dx-cell--ok-1 { background: #cde2fb; color: #0b0b0b; }
.dx-cell--ok-2 { background: #86b6ef; color: #0b0b0b; }
.dx-cell--ok-3 { background: #3987e5; color: #0b0b0b; }
.dx-cell--ok-4 { background: #1c5cab; color: #ffffff; }
.dx-cell--ok-5 { background: #0d366b; color: #ffffff; }
.dx-cell--err-1 { background: color-mix(in srgb, #eb6834 25%, #ffffff); color: #0b0b0b; }
.dx-cell--err-2 { background: color-mix(in srgb, #eb6834 45%, #ffffff); color: #0b0b0b; }
.dx-cell--err-3 { background: color-mix(in srgb, #eb6834 65%, #ffffff); color: #0b0b0b; }
.dx-cell--err-4 { background: color-mix(in srgb, #eb6834 85%, #ffffff); color: #0b0b0b; }
.dx-cell--err-5 { background: #eb6834; color: #0b0b0b; }
.dx-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem 1.1rem;
  font-size: 0.82rem;
  color: var(--dx-muted);
  margin-top: 0.5rem;
}
.dx-swatch {
  display: inline-block;
  width: 0.8rem;
  height: 0.8rem;
  border-radius: 0.2rem;
  margin-right: 0.35rem;
  vertical-align: -1px;
}
.dx-empty {
  border: 1px dashed var(--dx-line);
  border-radius: 1rem;
  padding: 2.2rem 1.5rem;
  text-align: center;
  background: var(--dx-soft);
  margin-top: 1rem;
}
.dx-empty__title { font-size: 1.25rem; font-weight: 700; margin-bottom: 0.4rem; }
.dx-empty__hint { color: var(--dx-muted); margin-bottom: 0.9rem; }
.dx-empty code { font-size: 0.9rem; }
@media (max-width: 640px) {
  .block-container { padding-left: 1rem; padding-right: 1rem; }
  .dx-header { gap: 0.65rem; }
  .dx-title { font-size: 1.5rem; }
  .dx-card--hero .dx-card__value { font-size: 2.6rem; }
}
"""


def theme_css(max_width: str) -> str:
    return BASE_CSS.replace("__MAX_WIDTH__", max_width)


def inject_theme(wide: bool) -> None:
    max_width = DASHBOARD_MAX_WIDTH if wide else CHAT_MAX_WIDTH
    st.markdown(f"<style>{theme_css(max_width)}</style>", unsafe_allow_html=True)
