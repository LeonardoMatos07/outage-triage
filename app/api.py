import sqlite3
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, FastAPI

from app.database import connect, initialize
from app.llm import classify
from app.mock_llm import mock_classify
from app.pipeline import Classifier, run_triage
from app.schemas import TriageRequest, TriageResponse
from app.settings import database_path, is_mock_mode

app = FastAPI(title="Outage Triage")


def get_connection() -> Iterator[sqlite3.Connection]:
    connection = connect(database_path())
    initialize(connection)
    try:
        yield connection
    finally:
        connection.close()


def get_classifier() -> Classifier:
    return mock_classify if is_mock_mode() else classify


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/triage")
def triage(
    request: TriageRequest,
    connection: Annotated[sqlite3.Connection, Depends(get_connection)],
    classifier: Annotated[Classifier, Depends(get_classifier)],
) -> TriageResponse:
    return run_triage(connection, request.message, request.session_id, classifier)
