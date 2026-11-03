from pathlib import Path

import pytest

from app.llm import LlmResponse
from app.rules import matches_emergency_keyword
from app.schemas import TriageResult
from eval.dataset import DEV_PATH, TEST_PATH, EvalExample, load_examples
from eval.report import (
    load_latest_report,
    render_comparison,
    render_report,
    same_run_reports,
    write_comparison,
    write_report,
)
from eval.run_eval import confirmed, evaluate_model, main

ORACLE_CONFIDENCE = 0.95


class OracleClassifier:
    def __init__(self, examples: list[EvalExample], model: str = "claude-haiku-5-5") -> None:
        self.by_message = {example.message: example for example in examples}
        self.model = model

    def __call__(self, message: str) -> LlmResponse:
        example = self.by_message[message]
        result = TriageResult(
            intent=example.intent,
            is_emergency=example.is_emergency,
            neighborhood_raw=example.expected_neighborhood,
            street_or_reference=None,
            outage_since=None,
            scope=example.scope,
            confidence=ORACLE_CONFIDENCE,
            notes="",
        )
        return LlmResponse(
            result=result,
            model=self.model,
            input_tokens=1000,
            output_tokens=100,
            latency_seconds=0.5,
        )


@pytest.mark.parametrize("path", [DEV_PATH, TEST_PATH])
def test_labels_agree_with_pipeline_when_llm_is_perfect(path: Path) -> None:
    examples = load_examples(path)
    report = evaluate_model("claude-haiku-5-5", "dev", examples, 0, OracleClassifier(examples))
    assert report.metrics.action_accuracy.value == 1.0
    assert report.metrics.emergency.recall.value == 1.0
    assert report.metrics.emergency.precision.value == 1.0
    assert report.metrics.injection_resistance.value == 1.0
    assert report.metrics.neighborhood_accuracy.value == 1.0
    assert report.emergency_errors == []
    assert report.injection_errors == []


def test_cost_per_message_uses_configured_pricing() -> None:
    examples = load_examples(DEV_PATH)[:5]
    report = evaluate_model("claude-haiku-5-5", "dev", examples, 0, OracleClassifier(examples))
    expected = (1000 * 0.10 + 100 * 0.50) / 1_000_000 * 5.4935
    assert report.metrics.cost_per_message_brl == pytest.approx(expected)


def test_report_files_round_trip_and_render(tmp_path: Path) -> None:
    examples = load_examples(DEV_PATH)[:10]
    report = evaluate_model("claude-haiku-5-5", "dev", examples, 3, OracleClassifier(examples))
    markdown_path, json_path = write_report(report, tmp_path)
    assert markdown_path.name.startswith("eval-")
    assert markdown_path.name.endswith("-dev-claude-haiku-5-5.md")
    assert json_path.suffix == ".json"
    loaded = load_latest_report(tmp_path)
    assert loaded == report
    text = markdown_path.read_text(encoding="utf-8")
    assert "premissas do autor" in text
    assert "Matriz de confusão" in text
    assert "Nenhum erro." in text
    assert "Linhas ignoradas por não estarem revisadas: 3" in text


def test_report_lists_every_emergency_error_with_its_message() -> None:
    examples = load_examples(DEV_PATH)
    oracle = OracleClassifier(examples)
    missed = next(
        example
        for example in examples
        if example.is_emergency and not matches_emergency_keyword(example.message)
    )

    def blind_classifier(message: str) -> LlmResponse:
        response = oracle(message)
        if message == missed.message and response.result:
            return LlmResponse(
                result=response.result.model_copy(update={"is_emergency": False}),
                model=response.model,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                latency_seconds=response.latency_seconds,
            )
        return response

    report = evaluate_model("claude-haiku-5-5", "dev", examples, 0, blind_classifier)
    ids = [error.id for error in report.emergency_errors]
    assert ids == [missed.id]
    assert missed.message in render_report(report)


def test_comparison_table_has_one_row_per_model(tmp_path: Path) -> None:
    examples = load_examples(DEV_PATH)[:10]
    reports = [
        evaluate_model(model, "dev", examples, 0, OracleClassifier(examples, model))
        for model in ("claude-haiku-5-5", "claude-sonnet-5-5")
    ]
    text = render_comparison(reports)
    assert "claude-haiku-5-5" in text
    assert "claude-sonnet-5-5" in text
    path = write_comparison(reports, tmp_path)
    assert path.name.startswith("comparison-")
    for report in reports:
        write_report(report, tmp_path)
    latest = load_latest_report(tmp_path)
    assert latest is not None
    assert len(same_run_reports(latest, tmp_path)) == 2


def test_latest_report_is_none_for_empty_directory(tmp_path: Path) -> None:
    assert load_latest_report(tmp_path) is None


def test_confirmation_is_required_above_twenty_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "n")
    assert confirmed(20, assume_yes=False)
    assert not confirmed(21, assume_yes=False)
    assert confirmed(21, assume_yes=True)
    monkeypatch.setattr("builtins.input", lambda _: "y")
    assert confirmed(150, assume_yes=False)


def test_main_refuses_to_run_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert main(["--model", "claude-haiku-5-5", "--split", "dev"]) == 2
