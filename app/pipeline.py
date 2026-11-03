import sqlite3
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime

import anthropic

from app.attendance_log import AttendanceEntry, record_attendance
from app.llm import LlmResponse, classify, configured_model
from app.neighborhoods import match_neighborhood
from app.outages import Outage, find_active_outage, open_ticket
from app.pricing import estimate_cost_brl
from app.responses import render_reply, simulation_notice
from app.rules import DecisionInputs, decide, is_emergency
from app.schemas import Action, Decision, TicketKind, TriageResponse
from app.sessions import Session, clear_session, load_session, save_session

Classifier = Callable[[str], LlmResponse]

TICKET_KINDS = {
    Action.TICKET_MY_HOME: TicketKind.MY_HOME,
    Action.TICKET_POSSIBLE_NEW_OUTAGE: TicketKind.POSSIBLE_NEW_OUTAGE,
}


def classify_or_fail(classifier: Classifier, message: str) -> LlmResponse:
    started_at = time.perf_counter()
    try:
        return classifier(message)
    except anthropic.APIError:
        return LlmResponse(
            result=None,
            model=configured_model(),
            input_tokens=0,
            output_tokens=0,
            latency_seconds=time.perf_counter() - started_at,
        )


def update_session(
    connection: sqlite3.Connection,
    session_id: str,
    session: Session,
    decision: Decision,
    full_message: str,
) -> None:
    if decision.action is Action.ASK_NEIGHBORHOOD:
        save_session(
            connection,
            session_id,
            Session(session.neighborhood_asks + 1, full_message),
        )
    else:
        clear_session(connection, session_id)


def run_triage(
    connection: sqlite3.Connection,
    message: str,
    session_id: str | None = None,
    classifier: Classifier = classify,
) -> TriageResponse:
    active_session_id = session_id or str(uuid.uuid4())
    session = load_session(connection, active_session_id)
    full_message = f"{session.pending_message}\n{message}" if session.pending_message else message
    llm_response = classify_or_fail(classifier, full_message)
    triage = llm_response.result

    neighborhood = match_neighborhood(triage.neighborhood_raw if triage else None)
    active_outage: Outage | None = (
        find_active_outage(connection, neighborhood) if neighborhood else None
    )
    decision = decide(
        DecisionInputs(
            emergency=is_emergency(full_message, triage.is_emergency if triage else False),
            triage=triage,
            neighborhood=neighborhood,
            has_active_outage=active_outage is not None,
            neighborhood_questions_asked=session.neighborhood_asks,
        )
    )

    now = datetime.now(UTC)
    protocol = active_outage.protocol if active_outage else None
    ticket_kind = TICKET_KINDS.get(decision.action)
    if ticket_kind and triage and neighborhood:
        protocol = open_ticket(
            connection,
            neighborhood,
            ticket_kind,
            triage.street_or_reference,
            triage.outage_since,
            now,
        )

    reply = render_reply(
        decision.action,
        neighborhood=neighborhood,
        protocol=protocol,
        estimated_restoration=active_outage.estimated_restoration if active_outage else None,
        queue=decision.handoff.queue if decision.handoff else None,
    )
    update_session(connection, active_session_id, session, decision, full_message)
    record_attendance(
        connection,
        AttendanceEntry(
            created_at=now,
            message=message,
            triage_result=triage,
            action=decision.action,
            handoff_reason=decision.handoff.reason if decision.handoff else None,
            model=llm_response.model,
            input_tokens=llm_response.input_tokens,
            output_tokens=llm_response.output_tokens,
            cost_brl=estimate_cost_brl(
                llm_response.model, llm_response.input_tokens, llm_response.output_tokens
            ),
            latency_seconds=llm_response.latency_seconds,
        ),
    )
    return TriageResponse(
        session_id=active_session_id,
        reply=reply,
        action=decision.action,
        handed_to_human=decision.handoff is not None,
        handoff_reason=decision.handoff.reason if decision.handoff else None,
        queue=decision.handoff.queue if decision.handoff else None,
        priority=decision.handoff.priority if decision.handoff else None,
        protocol=protocol,
        notice=simulation_notice(),
    )
