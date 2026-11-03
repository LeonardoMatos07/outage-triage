from app.schemas import TriageResponse
from app.texts import load_texts

UI_TEXTS = "ui_pt.yaml"


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


def outcome_label(response: TriageResponse) -> str:
    chat_texts = load_texts(UI_TEXTS)["chat"]
    return str(chat_texts["handed_to_human" if response.handed_to_human else "automatic"])
