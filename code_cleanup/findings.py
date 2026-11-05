from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Finding:
    line: int
    column: int
    code: str
    message: str
    is_error: bool


@dataclass(frozen=True, slots=True)
class Cleaned:
    text: str
    findings: tuple[Finding, ...]


@dataclass(frozen=True, slots=True)
class FileResult:
    path: Path
    language: str
    is_changed: bool
    findings: tuple[Finding, ...]


def group_by_path(issues: list[tuple[Path, Finding]]) -> dict[Path, list[Finding]]:
    grouped = dict[Path, list[Finding]]()

    for path, finding in issues:
        grouped[path] = [*grouped.get(path, []), finding]

    return grouped


def all_findings(results: list[FileResult]) -> list[Finding]:
    findings = list[Finding]()

    for result in results:
        findings.extend(result.findings)

    return findings
