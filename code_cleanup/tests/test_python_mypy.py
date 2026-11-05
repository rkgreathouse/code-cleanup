from dataclasses import replace
from pathlib import Path
from subprocess import CompletedProcess

from ..python.mypy import find_failure, find_type_errors
from ..settings import load_settings


def test_reports_type_errors_against_the_cleaned_text(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None).python
    path = tmp_path / "a.py"

    findings = find_type_errors(tmp_path, {path: 'x: int = "a"\n'}, settings)

    assert [(item.code, item.line, item.column) for item in findings[path]] == [
        ("mypy:assignment", 1, 10)
    ]


def test_leaves_no_cache_in_the_project(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None).python

    find_type_errors(tmp_path, {tmp_path / "a.py": "x = 1\n"}, settings)

    assert list(tmp_path.iterdir()) == []


def test_turns_a_blocking_error_into_one_finding(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None).python
    texts = {tmp_path / "one" / "main.py": "", tmp_path / "two" / "main.py": ""}

    findings = find_type_errors(tmp_path, texts, settings)

    assert [item.code for item in findings[tmp_path]] == ["mypy"]


def test_can_be_switched_off(tmp_path: Path) -> None:
    settings = replace(load_settings(tmp_path, None).python, mypy_enabled=False)

    assert (
        find_type_errors(tmp_path, {tmp_path / "a.py": "x: int = 'a'\n"}, settings)
        == {}
    )


def test_a_mypy_that_cannot_run_is_reported_not_skipped() -> None:
    missing = CompletedProcess([], 1, stdout="", stderr="No module named mypy\n")
    found = CompletedProcess([], 1, stdout='{"file": "a.py"}\n', stderr="")

    assert find_failure(missing) == "No module named mypy"
    assert find_failure(found) is None
