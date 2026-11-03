import os
import time
from dataclasses import dataclass
from pathlib import Path

import anthropic
from pydantic import ValidationError

from app.schemas import TriageResult

DEFAULT_MODEL = "claude-haiku-5-5"
MAX_ATTEMPTS = 2
MAX_OUTPUT_TOKENS = 512
TOOL_NAME = "record_triage"
PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "triage.md"


@dataclass(frozen=True)
class LlmResponse:
    result: TriageResult | None
    model: str
    input_tokens: int
    output_tokens: int
    latency_seconds: float


def configured_model() -> str:
    return os.environ.get("LLM_MODEL", DEFAULT_MODEL)


def load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def triage_tool() -> anthropic.types.ToolParam:
    return {
        "name": TOOL_NAME,
        "description": "Record the structured triage of the customer message.",
        "input_schema": TriageResult.model_json_schema(),
    }


def wrap_customer_message(message: str) -> str:
    return f"<customer_message>\n{message}\n</customer_message>"


def parse_tool_input(response: anthropic.types.Message) -> TriageResult | None:
    for block in response.content:
        if block.type == "tool_use" and block.name == TOOL_NAME:
            try:
                return TriageResult.model_validate(block.input)
            except ValidationError:
                return None
    return None


def classify(
    message: str,
    client: anthropic.Anthropic | None = None,
    model: str | None = None,
) -> LlmResponse:
    active_client = client or anthropic.Anthropic()
    active_model = model or configured_model()
    system_prompt = load_system_prompt()
    input_tokens = 0
    output_tokens = 0
    result = None
    started_at = time.perf_counter()
    for _ in range(MAX_ATTEMPTS):
        response = active_client.messages.create(
            model=active_model,
            max_tokens=MAX_OUTPUT_TOKENS,
            system=system_prompt,
            tools=[triage_tool()],
            tool_choice={"type": "tool", "name": TOOL_NAME},
            messages=[{"role": "user", "content": wrap_customer_message(message)}],
        )
        input_tokens += response.usage.input_tokens
        output_tokens += response.usage.output_tokens
        result = parse_tool_input(response)
        if result is not None:
            break
    return LlmResponse(
        result=result,
        model=active_model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_seconds=time.perf_counter() - started_at,
    )
