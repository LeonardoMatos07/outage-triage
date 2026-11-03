import sqlite3
from datetime import UTC, datetime

import pytest

from app.neighborhoods import load_neighborhoods, match_neighborhood
from app.outages import find_active_outage, open_ticket
from app.pricing import estimate_cost_brl
from app.responses import format_forecast, render_reply
from app.schemas import Action, Queue, TicketKind


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Pituba", "Pituba"),
        ("pituba", "Pituba"),
        ("PITUBA!!", "Pituba"),
        ("Rio Vermlho", "Rio Vermelho"),
        ("caminho das arvores", "Caminho das Árvores"),
        ("Itapua", "Itapuã"),
        ("Federaçao", "Federação"),
    ],
)
def test_neighborhood_is_normalized(raw: str, expected: str) -> None:
    assert match_neighborhood(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "   ", "perto da padaria", "Lisboa"])
def test_unidentified_neighborhood_returns_none(raw: str | None) -> None:
    assert match_neighborhood(raw) is None


def test_every_neighborhood_matches_itself() -> None:
    for name in load_neighborhoods():
        assert match_neighborhood(name) == name


def test_active_outage_is_found_by_neighborhood(connection: sqlite3.Connection) -> None:
    outage = find_active_outage(connection, "Pituba")
    assert outage is not None
    assert outage.protocol == "OC-0001"
    assert outage.estimated_restoration == "2026-11-03T14:00:00"


def test_resolved_outage_is_ignored(connection: sqlite3.Connection) -> None:
    assert find_active_outage(connection, "Barra") is None


def test_neighborhood_without_outage_returns_none(connection: sqlite3.Connection) -> None:
    assert find_active_outage(connection, "Brotas") is None


def test_tickets_get_sequential_protocols(connection: sqlite3.Connection) -> None:
    now = datetime(2026, 11, 3, 10, 0, tzinfo=UTC)
    first = open_ticket(connection, "Brotas", TicketKind.MY_HOME, None, None, now)
    second = open_ticket(connection, "Brotas", TicketKind.MY_HOME, "Rua A", "desde 6h", now)
    assert (first, second) == ("CH-000001", "CH-000002")


def test_known_outage_reply_fills_protocol_neighborhood_and_forecast() -> None:
    reply = render_reply(
        Action.KNOWN_OUTAGE,
        neighborhood="Pituba",
        protocol="OC-0001",
        estimated_restoration="2026-11-03T14:00:00",
    )
    assert "OC-0001" in reply
    assert "Pituba" in reply
    assert "03/11 às 14:00" in reply


def test_missing_forecast_uses_fixed_phrase() -> None:
    assert format_forecast(None) == "ainda sem previsão cadastrada"


def test_handoff_reply_names_the_queue() -> None:
    assert "contas" in render_reply(Action.HANDOFF, queue=Queue.BILLING)


def test_emergency_reply_has_safety_guidance() -> None:
    reply = render_reply(Action.EMERGENCY)
    assert "não se aproxime" in reply
    assert "pessoas e animais" in reply


def test_cost_is_computed_from_configured_prices() -> None:
    pricing = {
        "usd_to_brl": 5.0,
        "models": {
            "m": {"input_usd_per_million_tokens": 1.0, "output_usd_per_million_tokens": 5.0}
        },
    }
    assert estimate_cost_brl("m", 1_000_000, 200_000, pricing) == pytest.approx(10.0)


def test_cost_is_unknown_when_prices_are_not_configured() -> None:
    assert estimate_cost_brl("unknown", 100, 10, {"usd_to_brl": 5.0, "models": {}}) is None
    missing_rate = {
        "usd_to_brl": None,
        "models": {
            "m": {"input_usd_per_million_tokens": 1.0, "output_usd_per_million_tokens": 5.0}
        },
    }
    assert estimate_cost_brl("m", 100, 10, missing_rate) is None


def test_repository_pricing_covers_both_evaluated_models() -> None:
    for model in ("claude-haiku-5-5", "claude-sonnet-5-5"):
        assert estimate_cost_brl(model, 1_000_000, 1_000_000) is not None
