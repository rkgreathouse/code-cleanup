import tempfile
from pathlib import Path

from ..findings import Cleaned, Finding
from ..settings import Settings
from .checks import find_style_issues
from .checkstyle import find_checkstyle_issues
from .errorprone import find_bug_patterns
from .format import format_java
from .layout import find_service_issues
from .logs import find_logging_issues
from .spacing import space_blocks
from .syntax import find_syntax_error, parse_java


def clean_java(text: str, path: Path, settings: Settings) -> Cleaned:
    java = settings.java

    if (error := find_syntax_error(parse_java(text))) is not None:
        return Cleaned(text=text, findings=(error,))

    formatted = format_java(text, path, java)

    if isinstance(formatted, Finding):
        return Cleaned(text=text, findings=(formatted,))

    spaced = space_blocks(formatted, java)
    tree = parse_java(spaced)
    findings = find_style_issues(tree, java) + find_logging_issues(tree, java)

    return Cleaned(text=spaced, findings=tuple(findings))


def check_java_project(
    root: Path, texts: dict[Path, str], settings: Settings
) -> dict[Path, list[Finding]]:
    # a file that does not parse is already reported, and would stop javac outright
    parsed = {
        path: text
        for path, text in texts.items()
        if find_syntax_error(parse_java(text)) is None
    }
    paths = sorted(parsed)

    if not paths:
        return {}

    with tempfile.TemporaryDirectory(prefix="code-cleanup-") as mirror_name:
        mirror = Path(mirror_name)
        write_mirror(mirror, root, parsed)
        lint = find_checkstyle_issues(mirror, root, paths, settings.java)
        bugs = find_bug_patterns(mirror, root, paths, settings.java)

    layout = find_service_issues(root, parsed) if settings.profile == "service" else {}

    return {
        path: [*lint.get(path, []), *bugs.get(path, []), *layout.get(path, [])]
        for path in lint.keys() | bugs.keys() | layout.keys()
    }


def write_mirror(mirror: Path, root: Path, texts: dict[Path, str]) -> None:
    for path, text in texts.items():
        copy = mirror / path.relative_to(root)
        copy.parent.mkdir(parents=True, exist_ok=True)
        copy.write_text(text)
