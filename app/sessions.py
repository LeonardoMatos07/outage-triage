import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class Session:
    neighborhood_asks: int = 0
    pending_message: str | None = None


def load_session(connection: sqlite3.Connection, session_id: str) -> Session:
    row = connection.execute(
        "SELECT neighborhood_asks, pending_message FROM sessions WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    if row is None:
        return Session()
    return Session(row["neighborhood_asks"], row["pending_message"])


def save_session(connection: sqlite3.Connection, session_id: str, session: Session) -> None:
    connection.execute(
        "INSERT OR REPLACE INTO sessions (session_id, neighborhood_asks, pending_message) "
        "VALUES (?, ?, ?)",
        (session_id, session.neighborhood_asks, session.pending_message),
    )
    connection.commit()


def clear_session(connection: sqlite3.Connection, session_id: str) -> None:
    connection.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    connection.commit()
