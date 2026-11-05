import tomllib
from pathlib import Path

from ..findings import Cleaned, Finding
from ..settings import Settings
from .spacing import space_tables
from .taplo import format_toml


def clean_toml(text: str, path: Path, settings: Settings) -> Cleaned:
    try:
        tomllib.loads(text)

    except tomllib.TOMLDecodeError as error:
        return Cleaned(text=text, findings=(to_syntax_finding(error),))

    formatted = format_toml(text, path, settings.toml)
    spaced = (
        space_tables(formatted) if settings.toml.blank_line_before_tables else formatted
    )

    return Cleaned(text=spaced, findings=())


def to_syntax_finding(error: tomllib.TOMLDecodeError) -> Finding:
    return Finding(
        line=error.lineno,
        column=error.colno,
        code="CC000",
        message=f"invalid TOML, file left as is: {error.msg}",
        is_error=True,
    )
