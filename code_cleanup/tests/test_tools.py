from pathlib import Path

from ..tools import find_tool


def test_finds_the_pinned_tools_installed_with_code_cleanup() -> None:
    assert Path(find_tool("ruff")).name.startswith("ruff")
    assert Path(find_tool("taplo")).name.startswith("taplo")
