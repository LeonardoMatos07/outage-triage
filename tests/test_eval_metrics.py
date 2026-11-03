import pytest

from app.schemas import Action, Intent
from eval.dataset import EvalExample
from eval.metrics import (
    Prediction,
    compute_metrics,
    emergency_errors,
    evaluate_targets,
    injection_errors,
)


def make_example(**overrides: object) -> EvalExample:
    fields: dict[str, object] = {
        "id": "x-001",
        "message": "sem luz",
        "category": "outage",
        "intent": "outage",
        "is_emergency": False,
        "expected_neighborhood": "Pituba",
        "scope": "unknown",
        "expected_action": "known_outage",
        "tags": [],
        "label_status": "reviewed",
    }
    return EvalExample.model_validate({**fields, **overrides})


def make_prediction(
    example: EvalExample | None = None,
    action: Action = Action.KNOWN_OUTAGE,
    intent: Intent | None = Intent.OUTAGE,
    emergency: bool = False,
    keyword_emergency: bool = False,
    llm_emergency: bool = False,
    neighborhood: str | None = "Pituba",
    handed_to_human: bool = False,
    cost_brl: float | None = 0.001,
    latency_seconds: float = 1.0,
) -> Prediction:
    return Prediction(
        example=example or make_example(),
        action=action,
        intent=intent,
        emergency=emergency,
        keyword_emergency=keyword_emergency,
        llm_emergency=llm_emergency,
        neighborhood=neighborhood,
        handed_to_human=handed_to_human,
        cost_brl=cost_brl,
        latency_seconds=latency_seconds,
    )


def emergency_example(example_id: str) -> EvalExample:
    return make_example(
        id=example_id,
        category="emergency",
        is_emergency=True,
        expected_action="emergency",
        expected_neighborhood=None,
    )


def test_emergency_recall_combines_keywords_and_llm() -> None:
    predictions = [
        make_prediction(emergency_example("a"), emergency=True, keyword_emergency=True),
        make_prediction(emergency_example("b"), emergency=True, llm_emergency=True),
        make_prediction(emergency_example("c"), emergency=False),
    ]
    emergency = compute_metrics(predictions).emergency
    assert (emergency.recall.correct, emergency.recall.total) == (2, 3)
    assert (emergency.keyword_only_recall.correct, emergency.llm_only_recall.correct) == (1, 1)


def test_emergency_precision_counts_false_alarms() -> None:
    predictions = [
        make_prediction(emergency_example("a"), emergency=True),
        make_prediction(make_example(id="b"), emergency=True),
    ]
    precision = compute_metrics(predictions).emergency.precision
    assert (precision.correct, precision.total) == (1, 2)


def test_intent_accuracy_and_confusion_matrix() -> None:
    predictions = [
        make_prediction(),
        make_prediction(intent=Intent.BILLING),
        make_prediction(intent=None),
    ]
    metrics = compute_metrics(predictions)
    assert metrics.intent_accuracy.correct == 1
    assert metrics.intent_confusion == {"outage": {"outage": 1, "billing": 1, "none": 1}}


def test_neighborhood_accuracy_ignores_examples_without_neighborhood() -> None:
    predictions = [
        make_prediction(),
        make_prediction(neighborhood="Brotas"),
        make_prediction(make_example(expected_neighborhood=None), neighborhood=None),
    ]
    rate = compute_metrics(predictions).neighborhood_accuracy
    assert (rate.correct, rate.total) == (1, 2)


def test_action_accuracy_and_auto_resolution() -> None:
    predictions = [
        make_prediction(),
        make_prediction(action=Action.HANDOFF, handed_to_human=True),
    ]
    metrics = compute_metrics(predictions)
    assert metrics.action_accuracy.correct == 1
    assert metrics.auto_resolution.correct == 1


def test_injection_resistance_counts_only_tagged_examples() -> None:
    injected = make_example(id="i", tags=["prompt_injection"])
    predictions = [
        make_prediction(injected),
        make_prediction(injected, action=Action.HANDOFF),
        make_prediction(),
    ]
    metrics = compute_metrics(predictions)
    assert (metrics.injection_resistance.correct, metrics.injection_resistance.total) == (1, 2)
    errors = injection_errors(predictions)
    assert [(error.id, error.expected, error.predicted) for error in errors] == [
        ("i", "known_outage", "handoff")
    ]


def test_emergency_errors_list_misses_and_false_alarms() -> None:
    predictions = [
        make_prediction(emergency_example("miss"), emergency=False),
        make_prediction(make_example(id="alarm"), emergency=True),
        make_prediction(emergency_example("hit"), emergency=True),
    ]
    assert [error.id for error in emergency_errors(predictions)] == ["miss", "alarm"]


def test_cost_and_latency_statistics() -> None:
    predictions = [
        make_prediction(cost_brl=0.001, latency_seconds=latency)
        for latency in (1.0, 2.0, 3.0, 4.0, 10.0)
    ]
    metrics = compute_metrics(predictions)
    assert metrics.cost_per_message_brl == pytest.approx(0.001)
    assert metrics.latency.median_seconds == 3.0
    assert metrics.latency.p95_seconds == 10.0


def test_cost_is_unknown_when_any_cost_is_missing() -> None:
    predictions = [make_prediction(cost_brl=0.001), make_prediction(cost_brl=None)]
    assert compute_metrics(predictions).cost_per_message_brl is None


def test_empty_prediction_list_has_no_rates() -> None:
    metrics = compute_metrics([])
    assert metrics.intent_accuracy.value is None
    assert metrics.latency.median_seconds is None


def test_targets_flag_emergency_recall_below_100_percent() -> None:
    predictions = [
        make_prediction(emergency_example("a"), emergency=True),
        make_prediction(emergency_example("b"), emergency=False),
    ]
    targets = {t.name: t for t in evaluate_targets(compute_metrics(predictions))}
    assert not targets["emergency_recall"].met
    assert targets["emergency_recall"].value == 0.5
