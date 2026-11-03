import sqlite3
from dataclasses import dataclass
from datetime import datetime

from app.schemas import TicketKind

ACTIVE_STATUS = "active"


@dataclass(frozen=True)
class Outage:
    protocol: str
    neighborhood: str
    estimated_restoration: str | None


def find_active_outage(connection: sqlite3.Connection, neighborhood: str) -> Outage | None:
    row = connection.execute(
        "SELECT protocol, neighborhood, estimated_restoration FROM outages "
        "WHERE neighborhood = ? AND status = ? ORDER BY started_at LIMIT 1",
        (neighborhood, ACTIVE_STATUS),
    ).fetchone()
    if row is None:
        return None
    return Outage(row["protocol"], row["neighborhood"], row["estimated_restoration"])


def open_ticket(
    connection: sqlite3.Connection,
    neighborhood: str,
    kind: TicketKind,
    street_or_reference: str | None,
    outage_since: str | None,
    opened_at: datetime,
) -> str:
    cursor = connection.execute(
        "INSERT INTO tickets (neighborhood, kind, street_or_reference, outage_since, opened_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (neighborhood, kind.value, street_or_reference, outage_since, opened_at.isoformat()),
    )
    connection.commit()
    return f"CH-{cursor.lastrowid:06d}"
