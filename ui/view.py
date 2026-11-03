from enum import StrEnum

from app.schemas import Action, TriageResponse
from app.texts import load_texts

UI_TEXTS = "ui_pt.yaml"


class OutcomeKind(StrEnum):
    EMERGENCY = "emergency"
    QUESTION = "question"
    HANDOFF = "handoff"
    AUTOMATIC = "automatic"


def build_details(response: TriageResponse) -> dict[str, str]:
    fields = load_texts(UI_TEXTS)["chat"]["fields"]
    details = {fields["action"]: response.action.value}
    optional_values = {
        "queue": response.queue.value if response.queue else None,
        "priority": response.priority.value if response.priority else None,
        "protocol": response.protocol,
        "reason": response.handoff_reason.value if response.handoff_reason else None,
    }
    for key, value in optional_values.items():
        if value is not None:
            details[fields[key]] = value
    return details


def outcome_kind(response: TriageResponse) -> OutcomeKind:
    if response.action is Action.EMERGENCY:
        return OutcomeKind.EMERGENCY
    if response.action is Action.ASK_NEIGHBORHOOD:
        return OutcomeKind.QUESTION
    if response.handed_to_human:
        return OutcomeKind.HANDOFF
    return OutcomeKind.AUTOMATIC


def outcome_label(response: TriageResponse) -> str:
    outcomes = load_texts(UI_TEXTS)["chat"]["outcomes"]
    return str(outcomes[outcome_kind(response).value])
