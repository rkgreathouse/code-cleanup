from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .findings import Cleaned, Finding
from .ignore.clean import clean_ignore
from .java.clean import check_java_project, clean_java
from .python.clean import check_python_project, clean_python
from .settings import Settings
from .toml.clean import clean_toml

type ProjectCheck = Callable[
    [Path, dict[Path, str], Settings], dict[Path, list[Finding]]
]


@dataclass(frozen=True, slots=True)
class Language:
    name: str
    suffixes: tuple[str, ...]
    names: tuple[str, ...]
    clean: Callable[[str, Path, Settings], Cleaned]
    check_project: ProjectCheck | None


LANGUAGES = (
    Language(
        name="python",
        suffixes=(".py", ".pyi"),
        names=(),
        clean=clean_python,
        check_project=check_python_project,
    ),
    Language(
        name="java",
        suffixes=(".java",),
        names=(),
        clean=clean_java,
        check_project=check_java_project,
    ),
    Language(
        name="toml",
        suffixes=(".toml",),
        names=(),
        clean=clean_toml,
        check_project=None,
    ),
    Language(
        name="ignore",
        suffixes=(),
        names=(".gitignore", ".dockerignore"),
        clean=clean_ignore,
        check_project=None,
    ),
)


def route(path: Path) -> Language | None:
    for language in LANGUAGES:
        if path.suffix in language.suffixes or path.name in language.names:
            return language

    return None
