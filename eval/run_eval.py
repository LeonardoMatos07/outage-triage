import argparse
import os
import sys
from collections.abc import Callable
from functools import partial
from pathlib import Path

import anthropic

from app.database import connect, initialize
from app.llm import LlmResponse, classify
from app.mock_llm import mock_classify
from app.pipeline import PipelineOutcome, process_message
from app.pricing import estimate_cost_brl
from app.rules import matches_emergency_keyword
from app.settings import DEMO_REPORTS_DIR, MOCK_MODEL_NAME
from eval.dataset import DEV_PATH, TEST_PATH, EvalExample, load_examples, reviewed_only
from eval.metrics import (
    Prediction,
    compute_metrics,
    emergency_errors,
    injection_errors,
)
from eval.report import REPORTS_DIR, EvalReport, build_report, write_comparison, write_report

SPLIT_PATHS = {"dev": DEV_PATH, "test": TEST_PATH}
CONFIRMATION_THRESHOLD = 20

Classifier = Callable[[str], LlmResponse]


def to_prediction(example: EvalExample, outcome: PipelineOutcome) -> Prediction:
    triage = outcome.triage
    return Prediction(
        example=example,
        action=outcome.response.action,
        intent=triage.intent if triage else None,
        emergency=outcome.emergency,
        keyword_emergency=matches_emergency_keyword(example.message),
        llm_emergency=triage.is_emergency if triage else False,
        neighborhood=outcome.neighborhood,
        handed_to_human=outcome.response.handed_to_human,
        cost_brl=estimate_cost_brl(
            outcome.llm.model, outcome.llm.input_tokens, outcome.llm.output_tokens
        ),
        latency_seconds=outcome.llm.latency_seconds,
    )


def predict_all(examples: list[EvalExample], classifier: Classifier) -> list[Prediction]:
    connection = connect(":memory:")
    initialize(connection)
    try:
        return [
            to_prediction(example, process_message(connection, example.message, None, classifier))
            for example in examples
        ]
    finally:
        connection.close()


def evaluate_model(
    model: str,
    split: str,
    examples: list[EvalExample],
    ignored: int,
    classifier: Classifier,
) -> EvalReport:
    predictions = predict_all(examples, classifier)
    return build_report(
        model=model,
        split=split,
        examples_used=len(examples),
        ignored_unreviewed=ignored,
        metrics=compute_metrics(predictions),
        emergency_errors=emergency_errors(predictions),
        injection_errors=injection_errors(predictions),
    )


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="eval.run_eval")
    parser.add_argument("--model", nargs="+", default=[])
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--split", choices=sorted(SPLIT_PATHS), required=True)
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    if not args.mock and not args.model:
        parser.error("--model is required unless --mock is used")
    return args


def confirmed(total_calls: int, assume_yes: bool) -> bool:
    if assume_yes or total_calls <= CONFIRMATION_THRESHOLD:
        return True
    answer = input(f"This will make {total_calls} API calls. Continue? [y/N] ")
    return answer.strip().lower() in ("y", "yes")


def run_mock(args: argparse.Namespace, examples: list[EvalExample], ignored: int) -> int:
    output_dir = args.output_dir or DEMO_REPORTS_DIR
    report = evaluate_model(MOCK_MODEL_NAME, args.split, examples, ignored, mock_classify)
    markdown_path, json_path = write_report(report, output_dir)
    print(f"{MOCK_MODEL_NAME}: wrote {markdown_path} and {json_path}")
    return 0


def run_real(args: argparse.Namespace, examples: list[EvalExample], ignored: int) -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set")
        return 2
    if not confirmed(len(examples) * len(args.model), args.yes):
        print("aborted")
        return 1
    output_dir = args.output_dir or REPORTS_DIR
    client = anthropic.Anthropic()
    reports = []
    for model in args.model:
        classifier = partial(classify, client=client, model=model)
        report = evaluate_model(model, args.split, examples, ignored, classifier)
        markdown_path, json_path = write_report(report, output_dir)
        print(f"{model}: wrote {markdown_path} and {json_path}")
        reports.append(report)
    if len(reports) > 1:
        print(f"comparison: wrote {write_comparison(reports, output_dir)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    examples, ignored = reviewed_only(load_examples(SPLIT_PATHS[args.split]))
    print(f"{len(examples)} reviewed examples, {ignored} ignored (not reviewed)")
    if not examples:
        print("nothing to evaluate")
        return 1
    if args.mock:
        return run_mock(args, examples, ignored)
    return run_real(args, examples, ignored)


if __name__ == "__main__":
    sys.exit(main())
