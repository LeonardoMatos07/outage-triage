import os
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from app.schemas import (
    Action,
    Decision,
    Handoff,
    HandoffReason,
    Intent,
    Priority,
    Queue,
    Scope,
    TriageResult,
)

DEFAULT_CONFIDENCE_THRESHOLD = 0.7
KEYWORDS_PATH = Path(__file__).resolve().parent.parent / "data" / "emergency_keywords.yaml"


def normalize_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    letters_and_digits = re.sub(r"[^a-z0-9]+", " ", without_accents)
    return f" {letters_and_digits.strip()} "


@lru_cache
def load_emergency_keywords(path: Path = KEYWORDS_PATH) -> tuple[str, ...]:
    with path.open(encoding="utf-8") as file:
        raw_keywords = yaml.safe_load(file)["keywords"]
    return tuple(normalize_text(keyword) for keyword in raw_keywords)


def matches_emergency_keyword(message: str, keywords: tuple[str, ...] | None = None) -> bool:
    active_keywords = load_emergency_keywords() if keywords is None else keywords
    normalized_message = normalize_text(message)
    return any(keyword in normalized_message for keyword in active_keywords)


def is_emergency(message: str, llm_flagged_emergency: bool) -> bool:
    return matches_emergency_keyword(message) or llm_flagged_emergency


def confidence_threshold() -> float:
    return float(os.environ.get("CONFIDENCE_THRESHOLD", DEFAULT_CONFIDENCE_THRESHOLD))


def is_low_confidence(confidence: float, threshold: float | None = None) -> bool:
    active_threshold = confidence_threshold() if threshold is None else threshold
    return confidence < active_threshold


INTENT_QUEUES = {
    Intent.OUTAGE: Queue.OUTAGE,
    Intent.BILLING: Queue.BILLING,
    Intent.RECONNECTION: Queue.RECONNECTION,
    Intent.OTHER: Queue.GENERAL,
}

MAX_NEIGHBORHOOD_QUESTIONS = 1


@dataclass(frozen=True)
class DecisionInputs:
    emergency: bool
    triage: TriageResult | None
    neighborhood: str | None
    has_active_outage: bool
    neighborhood_questions_asked: int
    confidence_threshold: float | None = None


def handoff_decision(reason: HandoffReason, queue: Queue) -> Decision:
    return Decision(action=Action.HANDOFF, handoff=Handoff(reason=reason, queue=queue))


def decide_outage(inputs: DecisionInputs, triage: TriageResult) -> Decision:
    if inputs.neighborhood is None:
        if inputs.neighborhood_questions_asked >= MAX_NEIGHBORHOOD_QUESTIONS:
            return handoff_decision(HandoffReason.NEIGHBORHOOD_NOT_IDENTIFIED, Queue.OUTAGE)
        return Decision(action=Action.ASK_NEIGHBORHOOD)
    if inputs.has_active_outage:
        return Decision(action=Action.KNOWN_OUTAGE)
    if triage.scope is Scope.MY_HOME:
        return Decision(action=Action.TICKET_MY_HOME)
    return Decision(action=Action.TICKET_POSSIBLE_NEW_OUTAGE)


def decide(inputs: DecisionInputs) -> Decision:
    if inputs.emergency:
        emergency_handoff = Handoff(
            reason=HandoffReason.EMERGENCY, queue=Queue.EMERGENCY, priority=Priority.MAX
        )
        return Decision(action=Action.EMERGENCY, handoff=emergency_handoff)
    triage = inputs.triage
    if triage is None:
        return handoff_decision(HandoffReason.LLM_FAILURE, Queue.GENERAL)
    queue = INTENT_QUEUES[triage.intent]
    if is_low_confidence(triage.confidence, inputs.confidence_threshold):
        return handoff_decision(HandoffReason.LOW_CONFIDENCE, queue)
    if triage.intent is not Intent.OUTAGE:
        return handoff_decision(HandoffReason.UNSUPPORTED_INTENT, queue)
    return decide_outage(inputs, triage)
