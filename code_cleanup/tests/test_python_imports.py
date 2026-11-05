import ast
from pathlib import Path

from ..python.imports import find_absolute_self_imports, relativize_imports


def make_module(root: Path, *parts: str) -> Path:
    directory = root

    for part in parts[:-1]:
        directory = directory / part
        directory.mkdir(exist_ok=True)
        (directory / "__init__.py").write_text("")

    return directory / parts[-1]


def test_rewrites_own_package_imports_relative_to_the_module(tmp_path: Path) -> None:
    path = make_module(tmp_path, "tool", "lang", "parse.py")
    source = (
        "from tool.errors import ToolError\n"
        "from tool.lang import shared\n"
        "from tool.lang.read import read_file\n"
        "from other.errors import OtherError\n"
    )

    assert relativize_imports(source, path) == (
        "from ..errors import ToolError\n"
        "from . import shared\n"
        "from .read import read_file\n"
        "from other.errors import OtherError\n"
    )


def test_leaves_modules_outside_a_package_alone(tmp_path: Path) -> None:
    source = "from tool.errors import ToolError\n"

    assert relativize_imports(source, tmp_path / "script.py") == source


def test_still_flags_plain_imports_it_cannot_rewrite(tmp_path: Path) -> None:
    path = make_module(tmp_path, "tool", "scan.py")
    tree = ast.parse(
        "import tool.errors\nfrom .errors import ToolError\nimport utils\n"
    )

    findings = find_absolute_self_imports(tree, path)

    assert [(finding.code, finding.line) for finding in findings] == [("CC101", 1)]
