import logging
from dataclasses import dataclass
from pathlib import Path

from .errors import WriteError
from .findings import FileResult, Finding
from .router import LANGUAGES, route
from .settings import Settings

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CleanedFile:
    path: Path
    language: str
    text: str
    is_changed: bool
    findings: tuple[Finding, ...]


def clean_files(
    paths: list[Path], root: Path, settings: Settings, check: bool
) -> list[FileResult]:
    cleaned = [clean_file(path, settings, check) for path in paths]
    files = [item for item in cleaned if item is not None]
    project_findings = check_projects(root, files, settings)
    results = [
        to_result(item, root, project_findings.pop(item.path, ("", []))[1], settings)
        for item in files
    ]

    # project checks can point at paths no file pass produced, such as a folder
    for path, (language, findings) in sorted(project_findings.items()):
        results.append(
            FileResult(display_path(path, root), language, False, tuple(findings))
        )

    return sorted(results, key=lambda result: result.path)


def clean_file(path: Path, settings: Settings, check: bool) -> CleanedFile | None:
    language = route(path)

    if language is None:
        return None

    log.debug("cleaning %s as %s", path, language.name)
    original = read_text(path)

    # undecodable files are not source we can rewrite safely
    if original is None:
        log.warning("skipping %s: not UTF-8 text", path)
        return None

    cleaned = language.clean(original, path, settings)
    is_changed = cleaned.text != original

    if is_changed and not check:
        write_text(path, cleaned.text)

    return CleanedFile(path, language.name, cleaned.text, is_changed, cleaned.findings)


def check_projects(
    root: Path, files: list[CleanedFile], settings: Settings
) -> dict[Path, tuple[str, list[Finding]]]:
    combined = {}

    for language in LANGUAGES:
        texts = {
            item.path: item.text for item in files if item.language == language.name
        }

        if not texts or language.check_project is None:
            continue

        for path, findings in language.check_project(root, texts, settings).items():
            combined[path] = (language.name, findings)

    return combined


def to_result(
    item: CleanedFile, root: Path, extra: list[Finding], settings: Settings
) -> FileResult:
    findings = [*item.findings, *extra, *find_length_issues(item.text, settings)]
    ordered = sorted(findings, key=lambda finding: (finding.line, finding.column))

    return FileResult(
        path=display_path(item.path, root),
        language=item.language,
        is_changed=item.is_changed,
        findings=tuple(ordered),
    )


def display_path(path: Path, root: Path) -> Path:
    return path.relative_to(root) if path.is_relative_to(root) else path


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
