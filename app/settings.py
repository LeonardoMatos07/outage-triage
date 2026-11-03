import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
TEMPLATES_DIR = ROOT / "templates"
DEFAULT_NEIGHBORHOOD_MATCH_THRESHOLD = 85.0


def database_path() -> str:
    return os.environ.get("DATABASE_PATH", str(DATA_DIR / "outage_triage.db"))


def neighborhood_match_threshold() -> float:
    return float(
        os.environ.get("NEIGHBORHOOD_MATCH_THRESHOLD", DEFAULT_NEIGHBORHOOD_MATCH_THRESHOLD)
    )


MOCK_MODEL_NAME = "mock-heuristic"
DEMO_REPORTS_DIR = ROOT / "reports" / "demo"


def llm_mode() -> str:
    return os.environ.get("LLM_MODE", "real")


def is_mock_mode() -> bool:
    return llm_mode() == "mock"
