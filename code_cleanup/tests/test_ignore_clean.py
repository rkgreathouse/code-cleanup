from pathlib import Path

from ..ignore.clean import clean_ignore
from ..settings import load_settings


def clean(text: str, tmp_path: Path) -> str:
    return clean_ignore(
        text, tmp_path / ".gitignore", load_settings(tmp_path, None)
    ).text


def test_sorts_patterns_under_their_header(tmp_path: Path) -> None:
    text = "#Python\ndist/\n__pycache__/  \n\n\n\n# Editors\n.idea/\n.vscode/\n"

    assert clean(text, tmp_path) == (
        "# Python\n__pycache__/\ndist/\n\n# Editors\n.idea/\n.vscode/\n"
    )


def test_keeps_the_order_of_blocks_with_negations(tmp_path: Path) -> None:
    text = "# Logs\n*.log\n!keep.log\n"

    assert clean(text, tmp_path) == text


def test_drops_repeats_only_where_no_negation_intervenes(tmp_path: Path) -> None:
    text = "# A\n*.tmp\n*.tmp\n\n# B\n*.log\n!keep.log\n*.log\n"

    assert clean(text, tmp_path) == "# A\n*.tmp\n\n# B\n*.log\n!keep.log\n*.log\n"


def test_keeps_an_escaped_trailing_space(tmp_path: Path) -> None:
    assert clean("# Odd names\nname\\   \n", tmp_path) == "# Odd names\nname\\ \n"


def test_flags_blocks_without_a_header(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None)
    cleaned = clean_ignore("# A\nx\n\ny\n", tmp_path / ".gitignore", settings)

    assert [(item.code, item.line) for item in cleaned.findings] == [("CC401", 4)]


def test_cleaning_twice_changes_nothing(tmp_path: Path) -> None:
    once = clean("b\na\n\n\n#c\n!d\ne\n", tmp_path)

    assert clean(once, tmp_path) == once
