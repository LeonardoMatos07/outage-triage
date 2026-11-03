import pytest

from app.rules import DecisionInputs, decide
from app.schemas import Action, HandoffReason, Priority, Queue, TriageResult
from tests.conftest import make_triage


def make_inputs(
    emergency: bool = False,
    triage: TriageResult | None = None,
    neighborhood: str | None = "Pituba",
    has_active_outage: bool = False,
    neighborhood_questions_asked: int = 0,
    use_default_triage: bool = True,
) -> DecisionInputs:
    return DecisionInputs(
        emergency=emergency,
        triage=make_triage() if use_default_triage and triage is None else triage,
        neighborhood=neighborhood,
        has_active_outage=has_active_outage,
        neighborhood_questions_asked=neighborhood_questions_asked,
        confidence_threshold=0.7,
    )


def test_known_outage_when_active_outage_in_neighborhood() -> None:
    decision = decide(make_inputs(has_active_outage=True))
    assert decision.action is Action.KNOWN_OUTAGE
    assert decision.handoff is None


def test_individual_ticket_when_no_outage_and_scope_is_my_home() -> None:
    decision = decide(make_inputs(triage=make_triage(scope="my_home")))
    assert decision.action is Action.TICKET_MY_HOME
    assert decision.handoff is None


@pytest.mark.parametrize("scope", ["street_or_area", "unknown"])
def test_possible_new_outage_when_no_outage_and_wider_scope(scope: str) -> None:
    decision = decide(make_inputs(triage=make_triage(scope=scope)))
    assert decision.action is Action.TICKET_POSSIBLE_NEW_OUTAGE


def test_asks_neighborhood_the_first_time() -> None:
    decision = decide(make_inputs(neighborhood=None))
    assert decision.action is Action.ASK_NEIGHBORHOOD
    assert decision.handoff is None


def test_hands_off_when_neighborhood_still_unknown_after_asking() -> None:
    decision = decide(make_inputs(neighborhood=None, neighborhood_questions_asked=1))
    assert decision.action is Action.HANDOFF
    assert decision.handoff is not None
    assert decision.handoff.reason is HandoffReason.NEIGHBORHOOD_NOT_IDENTIFIED
    assert decision.handoff.queue is Queue.OUTAGE


def test_emergency_has_max_priority_handoff() -> None:
    decision = decide(make_inputs(emergency=True))
    assert decision.action is Action.EMERGENCY
    assert decision.handoff is not None
    assert decision.handoff.queue is Queue.EMERGENCY
    assert decision.handoff.priority is Priority.MAX


def test_emergency_wins_without_any_llm_result() -> None:
    decision = decide(make_inputs(emergency=True, use_default_triage=False))
    assert decision.action is Action.EMERGENCY


def test_emergency_wins_over_low_confidence() -> None:
    decision = decide(make_inputs(emergency=True, triage=make_triage(confidence=0.1)))
    assert decision.action is Action.EMERGENCY


def test_low_confidence_goes_to_human() -> None:
    decision = decide(make_inputs(triage=make_triage(confidence=0.5)))
    assert decision.handoff is not None
    assert decision.handoff.reason is HandoffReason.LOW_CONFIDENCE


def test_missing_llm_result_goes_to_human() -> None:
    decision = decide(make_inputs(use_default_triage=False))
    assert decision.handoff is not None
    assert decision.handoff.reason is HandoffReason.LLM_FAILURE


@pytest.mark.parametrize(
    ("intent", "queue"),
    [
        ("billing", Queue.BILLING),
        ("reconnection", Queue.RECONNECTION),
        ("other", Queue.GENERAL),
    ],
)
def test_unsupported_intents_go_to_the_right_queue(intent: str, queue: Queue) -> None:
    decision = decide(make_inputs(triage=make_triage(intent=intent)))
    assert decision.action is Action.HANDOFF
    assert decision.handoff is not None
    assert decision.handoff.reason is HandoffReason.UNSUPPORTED_INTENT
    assert decision.handoff.queue is queue
