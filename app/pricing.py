from pathlib import Path
from typing import Any

import yaml

from app.settings import DATA_DIR

PRICING_PATH = DATA_DIR / "pricing.yaml"
TOKENS_PER_MILLION = 1_000_000


def load_pricing(path: Path = PRICING_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        loaded: dict[str, Any] = yaml.safe_load(file)
    return loaded


def estimate_cost_brl(
    model: str,
    input_tokens: int,
    output_tokens: int,
    pricing: dict[str, Any] | None = None,
) -> float | None:
    config = load_pricing() if pricing is None else pricing
    model_prices = config["models"].get(model)
    exchange_rate = config["usd_to_brl"]
    if model_prices is None or exchange_rate is None:
        return None
    input_price = model_prices["input_usd_per_million_tokens"]
    output_price = model_prices["output_usd_per_million_tokens"]
    if input_price is None or output_price is None:
        return None
    cost_usd = (input_tokens * input_price + output_tokens * output_price) / TOKENS_PER_MILLION
    return float(cost_usd * exchange_rate)
