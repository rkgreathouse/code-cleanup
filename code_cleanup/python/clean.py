import ast
from pathlib import Path

from ..findings import Cleaned, Finding
from ..settings import Settings
from .checks import find_style_issues
from .imports import find_absolute_self_imports, relativize_imports
from .layout import find_layout_issues
from .logs import find_logging_issues
from .mypy import find_type_errors
from .ruff import find_lint, fix_lint, format_code
from .spacing import space_blocks


def clean_python(text: str, path: Path, settings: Settings) -> Cleaned:
    python = settings.python

    try:
        ast.parse(text)

    except SyntaxError as error:
        return Cleaned(text=text, findings=(to_syntax_finding(error),))

    relative = relativize_imports(text, path) if python.relative_imports else text
    fixed = fix_lint(relative, path, python)
    formatted = format_code(fixed, path, python)
    spaced = space_blocks(formatted, python)
    findings = find_lint(spaced, path, python)
    tree = ast.parse(spaced)
    findings += find_style_issues(tree, path, python)

    if python.relative_imports:
        findings += find_absolute_self_imports(tree, path)

    findings += find_logging_issues(tree, path, python)

    return Cleaned(text=spaced, findings=tuple(findings))


def to_syntax_finding(error: SyntaxError) -> Finding:
    return Finding(
        line=error.lineno or 1,
        column=error.offset or 1,
        code="CC000",
        message=f"syntax error, file left as is: {error.msg}",
        is_error=True,
    )


def check_python_project(
    root: Path, texts: dict[Path, str], settings: Settings
) -> dict[Path, list[Finding]]:
    # a file that does not parse is already reported, and would stop mypy outright
    parsed = {path: text for path, text in texts.items() if parses(text)}
    type_errors = find_type_errors(root, parsed, settings.python)
    layout = find_layout_issues(root, parsed) if settings.profile == "cli" else {}

    return {
        path: [*type_errors.get(path, []), *layout.get(path, [])]
        for path in type_errors.keys() | layout.keys()
    }


def parses(text: str) -> bool:
    try:
        ast.parse(text)

    except SyntaxError:
        return False

    return True
