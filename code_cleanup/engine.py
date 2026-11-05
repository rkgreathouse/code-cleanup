import logging
from pathlib import Path

from .errors import WriteError
from .findings import FileResult, Finding
from .router import route
from .settings import Settings

log = logging.getLogger(__name__)


def clean_files(
    paths: list[Path], root: Path, settings: Settings, check: bool
) -> list[FileResult]:
    results = []

    for path in paths:
        language = route(path)

        if language is None:
            continue

        log.debug("cleaning %s as %s", path, language.name)
        original = read_text(path)

        # undecodable files are not source we can rewrite safely
        if original is None:
            log.warning("skipping %s: not UTF-8 text", path)
            continue

        cleaned = language.clean(original, path, settings)
        is_changed = cleaned.text != original

        if is_changed and not check:
            write_text(path, cleaned.text)

        findings = cleaned.findings + find_length_issues(cleaned.text, settings)
        ordered = sorted(findings, key=lambda item: (item.line, item.column, item.code))
        results.append(
            FileResult(
                path=path.relative_to(root),
                language=language.name,
                is_changed=is_changed,
                findings=tuple(ordered),
            )
        )

    return results


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")

    except UnicodeDecodeError:
        return None


def write_text(path: Path, text: str) -> None:
    try:
        path.write_text(text, encoding="utf-8")

    except OSError as error:
        raise WriteError(f"could not write {path}: {error}") from error


def find_length_issues(text: str, settings: Settings) -> tuple[Finding, ...]:
    count = len(text.splitlines())

    if count > settings.max_lines:
        return (length_finding(count, f"over {settings.max_lines}; split it", True),)

    if count > settings.warn_lines:
        return (length_finding(count, f"over {settings.warn_lines}", False),)

    return ()


def length_finding(count: int, detail: str, is_error: bool) -> Finding:
    return Finding(
        line=1,
        column=1,
        code="CC001",
        message=f"file is {count} lines, {detail}",
        is_error=is_error,
    )
