import ast
from pathlib import Path

from ..python.checks import find_style_issues
from .test_python_spacing import make_settings


def make_package(tmp_path: Path) -> Path:
    package = tmp_path / "tool"
    package.mkdir()
    (package / "__init__.py").write_text("")

    return package / "scan.py"


def codes(source: str, path: Path) -> list[str]:
    findings = find_style_issues(ast.parse(source), path, make_settings())
    return [finding.code for finding in findings]


def test_flags_absolute_imports_of_the_own_package(tmp_path: Path) -> None:
    path = make_package(tmp_path)

    assert codes("from tool.errors import ToolError\n", path) == ["CC101"]
    assert codes("import tool.errors\n", path) == ["CC101"]


def test_allows_relative_and_foreign_imports(tmp_path: Path) -> None:
    path = make_package(tmp_path)

    assert codes("from .errors import ToolError\nimport utils.log\n", path) == []


def test_ignores_imports_outside_any_package(tmp_path: Path) -> None:
    assert codes("from tool.errors import ToolError\n", tmp_path / "script.py") == []


def test_flags_each_constant_past_the_limit(tmp_path: Path) -> None:
    source = "A = 1\nB = 2\nC = 3\nD: int = 4\nlog = 5\n__all__ = []\n"

    assert codes(source, tmp_path / "script.py") == ["CC102", "CC102"]
