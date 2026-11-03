from collections import Counter
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel

from app.neighborhoods import load_neighborhoods
from app.schemas import Action, Intent, Scope
from app.settings import DATA_DIR

EVAL_DIR = DATA_DIR / "eval"
DEV_PATH = EVAL_DIR / "dev.jsonl"
TEST_PATH = EVAL_DIR / "test.jsonl"


class Category(StrEnum):
    OUTAGE = "outage"
    EMERGENCY = "emergency"
    BILLING = "billing"
    RECONNECTION = "reconnection"
    OTHER = "other"


class Tag(StrEnum):
    TYPO = "typo"
    NO_PUNCTUATION = "no_punctuation"
    SLANG = "slang"
    TRANSCRIBED_AUDIO = "transcribed_audio"
    ALL_CAPS = "all_caps"
    ANGRY = "angry"
    TWO_INTENTS = "two_intents"
    LANDMARK_ONLY = "landmark_only"
    PROMPT_INJECTION = "prompt_injection"
    AMBIGUOUS = "ambiguous"
    UNKNOWN_NEIGHBORHOOD = "unknown_neighborhood"


class LabelStatus(StrEnum):
    DRAFT = "draft"
    REVIEWED = "reviewed"


class EvalExample(BaseModel):
    id: str
    message: str
    category: Category
    intent: Intent
    is_emergency: bool
    expected_neighborhood: str | None
    scope: Scope
    expected_action: Action
    tags: list[Tag]
    label_status: LabelStatus


CATEGORY_TARGETS = {
    Category.OUTAGE: 0.40,
    Category.EMERGENCY: 0.15,
    Category.BILLING: 0.15,
    Category.RECONNECTION: 0.10,
    Category.OTHER: 0.20,
}
CATEGORY_TOLERANCE = 0.03
DEV_SIZE_RANGE = (40, 60)
TEST_SIZE_RANGE = (90, 110)
REQUIRED_TAGS = (
    Tag.TYPO,
    Tag.NO_PUNCTUATION,
    Tag.SLANG,
    Tag.TRANSCRIBED_AUDIO,
    Tag.ALL_CAPS,
    Tag.ANGRY,
    Tag.TWO_INTENTS,
    Tag.LANDMARK_ONLY,
    Tag.PROMPT_INJECTION,
)
MIN_EXAMPLES_PER_TAG = 3
MIN_PROMPT_INJECTIONS = 5


def load_examples(path: Path) -> list[EvalExample]:
    with path.open(encoding="utf-8") as file:
        return [EvalExample.model_validate_json(line) for line in file if line.strip()]


def reviewed_only(examples: list[EvalExample]) -> tuple[list[EvalExample], int]:
    kept = [example for example in examples if example.label_status is LabelStatus.REVIEWED]
    return kept, len(examples) - len(kept)


def check_example_consistency(example: EvalExample, known_neighborhoods: set[str]) -> list[str]:
    problems = []
    if example.expected_neighborhood and example.expected_neighborhood not in known_neighborhoods:
        problems.append(f"{example.id}: unknown neighborhood {example.expected_neighborhood}")
    if example.is_emergency != (example.expected_action is Action.EMERGENCY):
        problems.append(f"{example.id}: is_emergency and expected_action disagree")
    if example.is_emergency != (example.category is Category.EMERGENCY):
        problems.append(f"{example.id}: is_emergency and category disagree")
    handoff_only = example.category in (Category.BILLING, Category.RECONNECTION, Category.OTHER)
    if handoff_only and example.expected_action is not Action.HANDOFF:
        problems.append(f"{example.id}: {example.category} must end in handoff")
    return problems


def check_split(name: str, examples: list[EvalExample], size_range: tuple[int, int]) -> list[str]:
    problems = []
    low, high = size_range
    if not low <= len(examples) <= high:
        problems.append(f"{name}: {len(examples)} examples, expected between {low} and {high}")
    ids = [example.id for example in examples]
    if len(ids) != len(set(ids)):
        problems.append(f"{name}: duplicated ids")
    return problems


def check_distribution(examples: list[EvalExample]) -> list[str]:
    problems = []
    counts = Counter(example.category for example in examples)
    for category, target in CATEGORY_TARGETS.items():
        share = counts[category] / len(examples)
        if abs(share - target) > CATEGORY_TOLERANCE:
            problems.append(
                f"category {category}: {share:.0%} of examples, target {target:.0%} "
                f"(tolerance {CATEGORY_TOLERANCE:.0%})"
            )
    return problems


def check_variety(examples: list[EvalExample]) -> list[str]:
    problems = []
    tag_counts = Counter(tag for example in examples for tag in example.tags)
    for tag in REQUIRED_TAGS:
        if tag_counts[tag] < MIN_EXAMPLES_PER_TAG:
            problems.append(
                f"tag {tag}: {tag_counts[tag]} examples, minimum {MIN_EXAMPLES_PER_TAG}"
            )
    if tag_counts[Tag.PROMPT_INJECTION] < MIN_PROMPT_INJECTIONS:
        problems.append(
            f"prompt injection: {tag_counts[Tag.PROMPT_INJECTION]} examples, "
            f"minimum {MIN_PROMPT_INJECTIONS}"
        )
    return problems


def check_no_leakage(dev: list[EvalExample], test: list[EvalExample]) -> list[str]:
    dev_messages = {example.message.strip().lower() for example in dev}
    return [
        f"{example.id}: message also present in dev"
        for example in test
        if example.message.strip().lower() in dev_messages
    ]


def check_dataset(dev: list[EvalExample], test: list[EvalExample]) -> list[str]:
    known_neighborhoods = set(load_neighborhoods())
    everything = dev + test
    problems = check_split("dev", dev, DEV_SIZE_RANGE) + check_split("test", test, TEST_SIZE_RANGE)
    for example in everything:
        problems += check_example_consistency(example, known_neighborhoods)
    ids = [example.id for example in everything]
    if len(ids) != len(set(ids)):
        problems.append("ids are not unique across dev and test")
    return (
        problems
        + check_distribution(everything)
        + check_variety(everything)
        + check_no_leakage(dev, test)
    )
