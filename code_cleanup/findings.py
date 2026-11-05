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
