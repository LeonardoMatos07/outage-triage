import sqlite3
from collections import Counter

from pydantic import BaseModel

from eval.metrics import LatencyStats, Rate, latency_stats_from, rate_of

RECENT_LIMIT = 20
EMERGENCY_ACTION = "emergency"


class RecentAttendance(BaseModel):
    created_at: str
    message: str
    action: str
    handoff_reason: str | None
    model: str


class LiveStats(BaseModel):
    total: int
    auto_resolution: Rate
    handed_to_human: int
    emergencies: int
    by_action: dict[str, int]
    by_handoff_reason: dict[str, int]
    average_cost_brl: float | None
    latency: LatencyStats
    recent: list[RecentAttendance]


def average_cost(costs: list[float | None]) -> float | None:
    known = [cost for cost in costs if cost is not None]
    if not costs or len(known) != len(costs):
        return None
    return sum(known) / len(known)


def load_recent(connection: sqlite3.Connection, limit: int) -> list[RecentAttendance]:
    rows = connection.execute(
        "SELECT created_at, message, action, handoff_reason, model "
        "FROM attendances ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [
        RecentAttendance(
            created_at=row["created_at"],
            message=row["message"],
            action=row["action"],
            handoff_reason=row["handoff_reason"],
            model=row["model"],
        )
        for row in rows
    ]


def load_live_stats(connection: sqlite3.Connection, recent_limit: int = RECENT_LIMIT) -> LiveStats:
    rows = connection.execute(
        "SELECT action, handed_to_human, handoff_reason, cost_brl, latency_seconds FROM attendances"
    ).fetchall()
    actions = Counter(row["action"] for row in rows)
    reasons = Counter(row["handoff_reason"] for row in rows if row["handoff_reason"])
    return LiveStats(
        total=len(rows),
        auto_resolution=rate_of([not row["handed_to_human"] for row in rows]),
        handed_to_human=sum(row["handed_to_human"] for row in rows),
        emergencies=actions[EMERGENCY_ACTION],
        by_action=dict(actions.most_common()),
        by_handoff_reason=dict(reasons.most_common()),
        average_cost_brl=average_cost([row["cost_brl"] for row in rows]),
        latency=latency_stats_from([row["latency_seconds"] for row in rows]),
        recent=load_recent(connection, recent_limit),
    )
