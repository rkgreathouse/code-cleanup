from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .findings import Cleaned
from .python.clean import clean_python
from .settings import Settings


@dataclass(frozen=True, slots=True)
class Language:
    name: str
    suffixes: tuple[str, ...]
    clean: Callable[[str, Path, Settings], Cleaned]


LANGUAGES = (Language(name="python", suffixes=(".py", ".pyi"), clean=clean_python),)


def route(path: Path) -> Language | None:
    for language in LANGUAGES:
        if path.suffix in language.suffixes:
            return language

    return None
