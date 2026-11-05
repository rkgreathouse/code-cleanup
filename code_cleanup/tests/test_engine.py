from dataclasses import replace
from pathlib import Path

from ..engine import clean_files
from ..settings import load_settings

MESSY = "def f(x):\n    if x:\n        return 1\n    return 2\n"


def test_fix_rewrites_files_in_place(tmp_path: Path) -> None:
    path = tmp_path / "a.py"
    path.write_text(MESSY)

    results = clean_files([path], tmp_path, load_settings(tmp_path, None), check=False)

    assert results[0].is_changed
    assert path.read_text() != MESSY


def test_check_reports_without_writing(tmp_path: Path) -> None:
    path = tmp_path / "a.py"
    path.write_text(MESSY)

    results = clean_files([path], tmp_path, load_settings(tmp_path, None), check=True)

    assert results[0].is_changed
    assert path.read_text() == MESSY


def test_skips_files_no_language_claims(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("hello\n")

    assert (
        clean_files([path], tmp_path, load_settings(tmp_path, None), check=True) == []
    )


def test_warns_then_fails_on_long_files(tmp_path: Path) -> None:
    path = tmp_path / "a.py"
    path.write_text("x = 1\n" * 5)
    settings = replace(load_settings(tmp_path, None), warn_lines=3, max_lines=4)

    results = clean_files([path], tmp_path, settings, check=True)

    assert [(item.code, item.is_error) for item in results[0].findings] == [
        ("CC001", True)
    ]
