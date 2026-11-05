import ast
from dataclasses import replace
from pathlib import Path

from ..python.checks import find_style_issues
from .test_python_spacing import make_settings


def codes(source: str, path: Path) -> list[str]:
    findings = find_style_issues(ast.parse(source), path, make_settings())
    return [finding.code for finding in findings]


def test_flags_environment_reads(tmp_path: Path) -> None:
    source = (
        "import os\nfrom os import getenv\nx = os.environ['A']\ny = os.getenv('B')\n"
    )

    assert codes(source, tmp_path / "a.py") == ["CC104", "CC104", "CC104"]


def test_flags_each_constant_past_the_limit(tmp_path: Path) -> None:
    source = "A = 1\nB = 2\nC = 3\nD: int = 4\nlog = 5\n__all__ = []\n"

    assert codes(source, tmp_path / "script.py") == ["CC102", "CC102"]


def test_flags_module_class_and_function_docstrings(tmp_path: Path) -> None:
    source = '"""Mod."""\nclass A:\n    """A."""\n    def f(self):\n        """F."""\n'

    assert codes(source, tmp_path / "script.py") == ["CC103", "CC103", "CC103"]


def test_docstrings_can_be_allowed(tmp_path: Path) -> None:
    settings = replace(make_settings(), allow_docstrings=True)
    findings = find_style_issues(ast.parse('"""Mod."""\n'), tmp_path / "a.py", settings)

    assert findings == []
