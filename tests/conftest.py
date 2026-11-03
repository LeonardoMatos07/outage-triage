import sqlite3
from collections.abc import Iterator
from typing import Any

import pytest

from app.database import connect, initialize
from app.llm import LlmResponse
from app.schemas import TriageResult

DEFAULT_TRIAGE: dict[str, Any] = {
    "intent": "outage",
    "is_emergency": False,
    "neighborhood_raw": "Pituba",
    "street_or_reference": None,
    "outage_since": None,
    "scope": "street_or_area",
    "confidence": 0.95,
    "notes": "",
}


def make_triage(**overrides: Any) -> TriageResult:
    return TriageResult.model_validate({**DEFAULT_TRIAGE, **overrides})


def make_llm_response(result: TriageResult | None) -> LlmResponse:
    return LlmResponse(
        result=result,
        model="test-model",
        input_tokens=120,
        output_tokens=30,
        latency_seconds=0.5,
    )


class ScriptedClassifier:
    def __init__(self, *results: TriageResult | None) -> None:
        self.remaining = list(results)
        self.received: list[str] = []

    def __call__(self, message: str) -> LlmResponse:
        self.received.append(message)
        return make_llm_response(self.remaining.pop(0))


@pytest.fixture
def connection() -> Iterator[sqlite3.Connection]:
    database = connect(":memory:")
    initialize(database)
    yield database
    database.close()
