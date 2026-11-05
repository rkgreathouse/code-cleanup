from pathlib import Path

from ..settings import load_settings
from ..toml.clean import clean_toml


def test_formats_then_spaces_tables(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None)

    cleaned = clean_toml("[a]\nx=1\n[b]\ny='z'\n", tmp_path / "a.toml", settings)

    assert cleaned.text == "[a]\nx = 1\n\n[b]\ny = 'z'\n"


def test_leaves_invalid_toml_unchanged(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None)

    cleaned = clean_toml("a = [\n", tmp_path / "a.toml", settings)

    assert cleaned.text == "a = [\n"
    assert [(item.code, item.line) for item in cleaned.findings] == [("CC000", 2)]
