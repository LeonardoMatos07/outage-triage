from eval.dataset import (
    DEV_PATH,
    TEST_PATH,
    EvalExample,
    LabelStatus,
    check_dataset,
    check_example_consistency,
    check_no_leakage,
    load_examples,
    reviewed_only,
)


def make_example(**overrides: object) -> EvalExample:
    fields: dict[str, object] = {
        "id": "x-001",
        "message": "sem luz na pituba",
        "category": "outage",
        "intent": "outage",
        "is_emergency": False,
        "expected_neighborhood": "Pituba",
        "scope": "unknown",
        "expected_action": "known_outage",
        "tags": [],
        "label_status": "draft",
    }
    return EvalExample.model_validate({**fields, **overrides})


def test_repository_datasets_pass_all_checks() -> None:
    assert check_dataset(load_examples(DEV_PATH), load_examples(TEST_PATH)) == []


def test_every_repository_row_starts_as_draft_or_reviewed() -> None:
    rows = load_examples(DEV_PATH) + load_examples(TEST_PATH)
    assert all(row.label_status in LabelStatus for row in rows)


def test_reviewed_only_counts_ignored_rows() -> None:
    examples = [make_example(), make_example(id="x-002", label_status="reviewed")]
    kept, ignored = reviewed_only(examples)
    assert [example.id for example in kept] == ["x-002"]
    assert ignored == 1


def test_unknown_neighborhood_is_reported() -> None:
    problems = check_example_consistency(make_example(expected_neighborhood="Atlantis"), {"Pituba"})
    assert any("unknown neighborhood" in problem for problem in problems)


def test_emergency_flag_must_match_action_and_category() -> None:
    problems = check_example_consistency(make_example(is_emergency=True), {"Pituba"})
    assert len(problems) == 2


def test_billing_must_end_in_handoff() -> None:
    example = make_example(category="billing", intent="billing", expected_action="known_outage")
    problems = check_example_consistency(example, {"Pituba"})
    assert any("must end in handoff" in problem for problem in problems)


def test_dev_message_repeated_in_test_is_reported() -> None:
    dev = [make_example(id="dev-001", message="Sem luz na Pituba ")]
    test = [make_example(id="test-001")]
    assert check_no_leakage(dev, test) == ["test-001: message also present in dev"]
