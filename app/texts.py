from functools import lru_cache
from typing import Any

import yaml

from app.settings import TEMPLATES_DIR


@lru_cache
def load_texts(file_name: str) -> dict[str, Any]:
    with (TEMPLATES_DIR / file_name).open(encoding="utf-8") as file:
        loaded: dict[str, Any] = yaml.safe_load(file)
    return loaded
