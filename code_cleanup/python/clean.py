import ast
from pathlib import Path

from ..findings import Cleaned, Finding
from ..settings import Settings
from .checks import find_style_issues
from .ruff import find_lint, fix_lint, format_code
from .spacing import space_blocks


def clean_python(text: str, path: Path, settings: Settings) -> Cleaned:
    python = settings.python

    try:
        ast.parse(text)

    except SyntaxError as error:
        return Cleaned(text=text, findings=(to_syntax_finding(error),))

    fixed = fix_lint(text, path, python)
    formatted = format_code(fixed, path, python)
    spaced = space_blocks(formatted, python)
    findings = find_lint(spaced, path, python)
    findings += find_style_issues(ast.parse(spaced), path, python)

    return Cleaned(text=spaced, findings=tuple(findings))


def to_syntax_finding(error: SyntaxError) -> Finding:
    return Finding(
        line=error.lineno or 1,
        column=error.offset or 1,
        code="CC000",
        message=f"syntax error, file left as is: {error.msg}",
        is_error=True,
    )
