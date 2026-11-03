from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.schemas import Action, Queue
from app.settings import TEMPLATES_DIR

TEMPLATES_PATH = TEMPLATES_DIR / "responses_pt.yaml"

TEMPLATE_KEYS = {
    Action.EMERGENCY: "emergency_safety",
    Action.KNOWN_OUTAGE: "known_outage",
    Action.TICKET_MY_HOME: "ticket_opened_my_home",
    Action.TICKET_POSSIBLE_NEW_OUTAGE: "ticket_opened_possible_outage",
    Action.ASK_NEIGHBORHOOD: "ask_neighborhood",
    Action.HANDOFF: "handoff_to_agent",
}


@lru_cache
def load_templates(path: Path = TEMPLATES_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        loaded: dict[str, Any] = yaml.safe_load(file)
    return loaded


def simulation_notice() -> str:
    return str(load_templates()["simulation_notice"])


def format_forecast(estimated_restoration: str | None) -> str:
    if estimated_restoration is None:
        return str(load_templates()["phrases"]["forecast_unavailable"])
    moment = datetime.fromisoformat(estimated_restoration)
    return moment.strftime("%d/%m às %H:%M")


def queue_label(queue: Queue) -> str:
    return str(load_templates()["queue_labels"][queue.value])


def render_reply(
    action: Action,
    neighborhood: str | None = None,
    protocol: str | None = None,
    estimated_restoration: str | None = None,
    queue: Queue | None = None,
) -> str:
    template = load_templates()["responses"][TEMPLATE_KEYS[action]]
    return str(
        template.format(
            neighborhood=neighborhood,
            protocol=protocol,
            forecast=format_forecast(estimated_restoration),
            queue_label=queue_label(queue) if queue else "",
        )
    )
