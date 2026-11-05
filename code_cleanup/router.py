from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .findings import Cleaned, Finding
from .python.clean import check_python_project, clean_python
from .settings import Settings


@dataclass(frozen=True, slots=True)
class Language:
    name: str
    suffixes: tuple[str, ...]
    clean: Callable[[str, Path, Settings], Cleaned]
    check_project: Callable[
        [Path, dict[Path, str], Settings], dict[Path, list[Finding]]
    ]


LANGUAGES = (
    Language(
        name="python",
        suffixes=(".py", ".pyi"),
        clean=clean_python,
        check_project=check_python_project,
    ),
)


def route(path: Path) -> Language | None:
    for language in LANGUAGES:
        if path.suffix in language.suffixes:
            return language

    return None
