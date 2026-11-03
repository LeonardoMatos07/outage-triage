from scripts.check_no_comments import find_comments, find_docstrings


def test_plain_comment_is_flagged() -> None:
    assert find_comments("x = 1  # explains x\n") == [1]


def test_tool_directives_are_allowed() -> None:
    source = "x = 1  # type: ignore[assignment]\ny = 2  # noqa: E501\n"
    assert find_comments(source) == []


def test_docstrings_are_flagged() -> None:
    source = 'def f() -> None:\n    "doc"\n\n\nclass C:\n    """doc"""\n'
    assert find_docstrings(source) == [2, 6]


def test_clean_source_passes() -> None:
    assert find_comments("x = 1\n") == []
    assert find_docstrings("def f() -> int:\n    return 1\n") == []
