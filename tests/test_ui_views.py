from html.parser import HTMLParser

from eval.dataset import DEV_PATH, load_examples
from eval.metrics import ErrorCase
from eval.report import EvalReport
from eval.run_eval import evaluate_model
from tests.test_eval_run import OracleClassifier
from ui.chat_view import (
    badge_html,
    details_html,
    header_html,
    mock_banner_html,
    notice_html,
    reply_html,
    strip_html,
)
from ui.dashboard_view import (
    best_models,
    comparison_html,
    confusion_cell_class,
    confusion_html,
    confusion_legend_html,
    empty_state_html,
    error_count_badge,
    errors_table_html,
    kpi_card_html,
    operation_kpis,
    ordered_labels,
    quality_kpis,
    run_summary_html,
    safety_alert_html,
    safety_kpis,
    section_html,
    title_html,
    value_kpi,
)
from ui.view import OutcomeKind


def make_report(model: str = "claude-haiku-5-5") -> EvalReport:
    examples = load_examples(DEV_PATH)
    return evaluate_model(model, "dev", examples, 0, OracleClassifier(examples, model))


def test_user_supplied_text_is_escaped_in_reply_and_details() -> None:
    html = reply_html("<script>alert(1)</script>", OutcomeKind.AUTOMATIC, "ok", None)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "<script>" not in details_html({"a": "<b>"})


def test_emergency_badge_uses_the_strong_style_and_an_icon_and_text() -> None:
    html = badge_html(OutcomeKind.EMERGENCY, "Emergência")
    assert "dx-badge--emergency" in html
    assert "⚠" in html
    assert "Emergência" in html


def test_welcome_reply_has_no_badge_or_protocol() -> None:
    html = reply_html("Olá", None, None, None)
    assert "dx-badge" not in html
    assert "dx-protocol" not in html


def test_strip_without_label_has_no_empty_strong_tag() -> None:
    assert "<strong>" not in strip_html("good", "✓", "", "texto")


def test_kpi_status_pairs_color_with_icon_and_text() -> None:
    report = make_report()
    kpis = safety_kpis(report)
    html = kpi_card_html(kpis["emergency_recall"], hero=True)
    assert "dx-card--met" in html
    assert "✓" in html
    assert "Meta atingida" in html
    assert "Meta (premissa)" in html
    assert "dx-meter__target" in html


def test_missed_target_is_flagged_with_cross_and_text() -> None:
    report = make_report()
    report = report.model_copy(
        update={
            "targets": [
                target.model_copy(update={"met": False})
                if target.name == "emergency_recall"
                else target
                for target in report.targets
            ]
        }
    )
    html = kpi_card_html(safety_kpis(report)["emergency_recall"], hero=True)
    assert "dx-card--missed" in html
    assert "✕" in html
    assert "Meta não atingida" in html


def test_metric_without_target_is_marked_as_tracking_only() -> None:
    html = kpi_card_html(safety_kpis(make_report())["emergency_precision"])
    assert "Sem meta: acompanhar" in html
    assert "dx-meter__target" not in html


def test_unavailable_metric_has_explicit_label() -> None:
    html = kpi_card_html(value_kpi("cost_per_message", None, "n/d", "detalhe"))
    assert "n/d" in html
    assert "Sem dados" in html


def test_kpi_groups_have_expected_sizes() -> None:
    report = make_report()
    assert len(quality_kpis(report)) == 3
    assert len(operation_kpis(report)) == 3
    assert set(safety_kpis(report)) == {
        "emergency_recall",
        "injection_resistance",
        "emergency_precision",
    }


def test_safety_alert_changes_with_missed_emergencies() -> None:
    report = make_report()
    assert "dx-strip--good" in safety_alert_html(report)
    recall = report.metrics.emergency.recall.model_copy(update={"correct": 0, "total": 3})
    broken = report.model_copy(
        update={
            "metrics": report.metrics.model_copy(
                update={"emergency": report.metrics.emergency.model_copy(update={"recall": recall})}
            )
        }
    )
    html = safety_alert_html(broken)
    assert "dx-strip--critical" in html
    assert "3 emergência(s)" in html


def test_errors_table_escapes_messages_and_empty_list_is_positive() -> None:
    errors = [
        ErrorCase(id="x-1", message="<i>fio</i>", expected="emergency", predicted="not_emergency")
    ]
    html = errors_table_html(errors)
    assert "&lt;i&gt;fio&lt;/i&gt;" in html
    assert "<i>" not in html
    assert "Nenhum erro." in errors_table_html([])


def test_confusion_levels_scale_with_count_and_split_hits_from_errors() -> None:
    assert confusion_cell_class(0, 10, True) == "dx-cell--zero"
    assert confusion_cell_class(10, 10, True) == "dx-cell--ok-5"
    assert confusion_cell_class(1, 10, False) == "dx-cell--err-1"
    assert confusion_cell_class(5, 10, False) == "dx-cell--err-3"


def test_confusion_matrix_has_headers_scope_and_all_cells() -> None:
    matrix = {"outage": {"outage": 4, "billing": 1}, "billing": {"billing": 2, "none": 1}}
    html = confusion_html(matrix)
    assert html.count('scope="col"') == 3
    assert html.count('scope="row"') == 2
    assert html.count("<td") == 6
    rows, columns = ordered_labels(matrix)
    assert rows == ["outage", "billing"]
    assert columns == ["outage", "billing", "none"]


def test_best_model_is_highlighted_per_column() -> None:
    first = make_report("claude-haiku-5-5")
    second = make_report("claude-sonnet-5-5")
    best = best_models([first, second])
    assert best["cost_per_message"] == {"claude-haiku-5-5"}
    assert best["emergency_recall"] == {"claude-haiku-5-5", "claude-sonnet-5-5"}


def test_empty_state_command_depends_on_mode() -> None:
    assert "make eval" in empty_state_html(False)
    assert "make demo-report" in empty_state_html(True)


class TagBalanceChecker(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if not self.stack or self.stack.pop() != tag:
            self.errors.append(tag)


def is_well_formed(html: str) -> bool:
    checker = TagBalanceChecker()
    checker.feed(html)
    return not checker.errors and not checker.stack


def test_every_generated_fragment_is_well_formed_html() -> None:
    report = make_report()
    errors = [ErrorCase(id="x", message="m", expected="a", predicted="b")]
    fragments = [
        header_html(),
        notice_html(),
        mock_banner_html(),
        reply_html("texto", OutcomeKind.AUTOMATIC, "ok", "OC-1"),
        details_html({"a": "b"}),
        title_html(),
        run_summary_html(report),
        safety_alert_html(report),
        errors_table_html(errors),
        errors_table_html([]),
        confusion_html(report.metrics.intent_confusion),
        confusion_legend_html(),
        comparison_html([report, make_report("claude-sonnet-5-5")]),
        empty_state_html(True),
        section_html("Titulo", error_count_badge(2)),
        *[kpi_card_html(kpi) for kpi in quality_kpis(report) + operation_kpis(report)],
        *[kpi_card_html(kpi, hero=True) for kpi in safety_kpis(report).values()],
    ]
    assert all(is_well_formed(fragment) for fragment in fragments)
    assert all("\n\n" not in fragment for fragment in fragments)
