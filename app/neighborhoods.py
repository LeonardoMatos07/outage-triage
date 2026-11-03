import csv
from functools import lru_cache
from pathlib import Path

from rapidfuzz import fuzz, process

from app.rules import normalize_text
from app.settings import DATA_DIR, neighborhood_match_threshold

NEIGHBORHOODS_PATH = DATA_DIR / "neighborhoods.csv"


@lru_cache
def load_neighborhoods(path: Path = NEIGHBORHOODS_PATH) -> tuple[str, ...]:
    with path.open(encoding="utf-8", newline="") as file:
        return tuple(row["name"] for row in csv.DictReader(file))


def match_neighborhood(
    raw: str | None,
    neighborhoods: tuple[str, ...] | None = None,
    threshold: float | None = None,
) -> str | None:
    if raw is None or not raw.strip():
        return None
    names = load_neighborhoods() if neighborhoods is None else neighborhoods
    cutoff = neighborhood_match_threshold() if threshold is None else threshold
    normalized_names = {name: normalize_text(name) for name in names}
    best = process.extractOne(
        normalize_text(raw), normalized_names, scorer=fuzz.ratio, score_cutoff=cutoff
    )
    if best is None:
        return None
    return str(best[2])
