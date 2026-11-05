from pathlib import Path

from ..python.ruff import find_lint, fix_lint, format_code, write_ruff_config
from ..settings import load_settings


def test_formats_with_the_house_line_length(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None).python
    source = "x = {'a':1}\n"

    assert format_code(source, tmp_path / "a.py", settings) == 'x = {"a": 1}\n'


def test_fix_removes_unused_imports(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None).python

    assert fix_lint("import os\n", tmp_path / "a.py", settings) == ""


def test_lint_reports_what_it_cannot_fix(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None).python
    findings = find_lint("print(1)\n", tmp_path / "a.py", settings)

    assert [(finding.code, finding.line) for finding in findings] == [("T201", 1)]


def test_entry_module_may_print(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None).python

    assert find_lint("print(1)\n", tmp_path / "__main__.py", settings) == []


def test_config_file_is_reused_for_the_same_style() -> None:
    assert write_ruff_config("line-length = 88\n") == write_ruff_config(
        "line-length = 88\n"
    )
