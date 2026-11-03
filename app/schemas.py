from enum import StrEnum

from pydantic import BaseModel, Field


class Intent(StrEnum):
    OUTAGE = "outage"
    BILLING = "billing"
    RECONNECTION = "reconnection"
    OTHER = "other"


class Scope(StrEnum):
    MY_HOME = "my_home"
    STREET_OR_AREA = "street_or_area"
    UNKNOWN = "unknown"


class TriageResult(BaseModel):
    intent: Intent
    is_emergency: bool
    neighborhood_raw: str | None
    street_or_reference: str | None
    outage_since: str | None
    scope: Scope
    confidence: float = Field(ge=0, le=1)
    notes: str


class Action(StrEnum):
    EMERGENCY = "emergency"
    KNOWN_OUTAGE = "known_outage"
    TICKET_MY_HOME = "ticket_my_home"
    TICKET_POSSIBLE_NEW_OUTAGE = "ticket_possible_new_outage"
    ASK_NEIGHBORHOOD = "ask_neighborhood"
    HANDOFF = "handoff"


class HandoffReason(StrEnum):
    EMERGENCY = "emergency"
    LOW_CONFIDENCE = "low_confidence"
    UNSUPPORTED_INTENT = "unsupported_intent"
    NEIGHBORHOOD_NOT_IDENTIFIED = "neighborhood_not_identified"
    LLM_FAILURE = "llm_failure"


class Queue(StrEnum):
    EMERGENCY = "emergency"
    OUTAGE = "outage"
    BILLING = "billing"
    RECONNECTION = "reconnection"
    GENERAL = "general"


class Priority(StrEnum):
    NORMAL = "normal"
    MAX = "max"


class TicketKind(StrEnum):
    MY_HOME = "my_home"
    POSSIBLE_NEW_OUTAGE = "possible_new_outage"


class Handoff(BaseModel, frozen=True):
    reason: HandoffReason
    queue: Queue
    priority: Priority = Priority.NORMAL


class Decision(BaseModel, frozen=True):
    action: Action
    handoff: Handoff | None = None


class TriageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None


class TriageResponse(BaseModel):
    session_id: str
    reply: str
    action: Action
    handed_to_human: bool
    handoff_reason: HandoffReason | None
    queue: Queue | None
    priority: Priority | None
    protocol: str | None
    notice: str
