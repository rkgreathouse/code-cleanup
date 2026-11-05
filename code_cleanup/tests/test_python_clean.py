from pathlib import Path

from ..python.clean import clean_python
from ..settings import load_settings


def test_runs_lint_fixes_format_and_spacing_in_order(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None)
    source = "import os\ndef f(x):\n    y=1\n    if x:\n        y=2\n    return y\n"

    cleaned = clean_python(source, tmp_path / "a.py", settings)

    assert cleaned.text == (
        "def f(x):\n    y = 1\n\n    if x:\n        y = 2\n\n    return y\n"
    )


def test_cleaning_twice_changes_nothing(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None)
    source = "for a in b:\n    # skip\n    if a:\n        continue\n"

    once = clean_python(source, tmp_path / "a.py", settings).text

    assert clean_python(once, tmp_path / "a.py", settings).text == once


def test_leaves_files_with_syntax_errors_unchanged(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None)

    cleaned = clean_python("def f(:\n", tmp_path / "a.py", settings)

    assert cleaned.text == "def f(:\n"
    assert [finding.code for finding in cleaned.findings] == ["CC000"]
