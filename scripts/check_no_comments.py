import ast
import io
import re
import sys
import tokenize
from pathlib import Path

CHECKED_DIRECTORIES = ("app", "ui", "eval", "scripts", "tests")
ALLOWED_DIRECTIVE = re.compile(r"^#\s*(type:\s*ignore\[[^\]]+\]|noqa:\s*\S+)")
DOCSTRING_HOLDERS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def find_comments(source: str) -> list[int]:
    lines = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.COMMENT and not ALLOWED_DIRECTIVE.match(token.string):
            lines.append(token.start[0])
    return lines


def find_docstrings(source: str) -> list[int]:
    lines = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, DOCSTRING_HOLDERS) and ast.get_docstring(node, clean=False) is not None:
            first_statement = node.body[0]
            lines.append(first_statement.lineno)
    return lines


def check_file(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    comment_lines = [f"{path}:{line}: comment" for line in find_comments(source)]
    docstring_lines = [f"{path}:{line}: docstring" for line in find_docstrings(source)]
    return comment_lines + docstring_lines


def collect_python_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for directory in CHECKED_DIRECTORIES:
        files.extend(sorted((root / directory).rglob("*.py")))
    return files


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    violations = [v for path in collect_python_files(root) for v in check_file(path)]
    for violation in violations:
        print(violation)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
