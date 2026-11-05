from pathlib import Path

from ..settings import load_settings
from ..toml.taplo import format_toml


def test_formats_with_the_house_indent_and_width(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None).toml
    text = "[a]\nx=1\nitems=[" + ", ".join(f'"item-{n}"' for n in range(12)) + "]\n"

    formatted = format_toml(text, tmp_path / "a.toml", settings)

    assert formatted.startswith('[a]\nx = 1\nitems = [\n    "item-0",\n')
