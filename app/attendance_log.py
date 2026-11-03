import sqlite3
from dataclasses import dataclass
from datetime import datetime

from app.schemas import Action, HandoffReason, TriageResult


@dataclass(frozen=True)
class AttendanceEntry:
    created_at: datetime
    message: str
    triage_result: TriageResult | None
    action: Action
    handoff_reason: HandoffReason | None
    model: str
    input_tokens: int
    output_tokens: int
    cost_brl: float | None
    latency_seconds: float


def record_attendance(connection: sqlite3.Connection, entry: AttendanceEntry) -> None:
    triage_json = entry.triage_result.model_dump_json() if entry.triage_result else None
    connection.execute(
        "INSERT INTO attendances (created_at, message, triage_result, action, handed_to_human, "
        "handoff_reason, model, input_tokens, output_tokens, cost_brl, latency_seconds) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            entry.created_at.isoformat(),
            entry.message,
            triage_json,
            entry.action.value,
            int(entry.handoff_reason is not None),
            entry.handoff_reason.value if entry.handoff_reason else None,
            entry.model,
            entry.input_tokens,
            entry.output_tokens,
            entry.cost_brl,
            entry.latency_seconds,
        ),
    )
    connection.commit()
