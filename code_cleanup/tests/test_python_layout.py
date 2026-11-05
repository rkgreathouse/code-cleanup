from pathlib import Path

from ..python.layout import find_layout_issues

ENTRY = """import argparse
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Options:
    verbose: bool


def main() -> int:
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def make_tool(root: Path, name: str = "tool") -> dict[Path, str]:
    return {
        root / name / "__init__.py": "",
        root / name / "__main__.py": ENTRY,
        root / name / "errors.py": "class ToolError(Exception): ...\n",
        root / name / "tests" / "__init__.py": "",
        root / name / "tests" / "test_main.py": "",
    }


def codes(root: Path, texts: dict[Path, str]) -> dict[str, list[str]]:
    issues = find_layout_issues(root, texts)

    return {
        path.relative_to(root).as_posix(): [finding.code for finding in findings]
        for path, findings in sorted(issues.items())
    }


def test_a_tool_shaped_like_the_skill_passes(tmp_path: Path) -> None:
    assert codes(tmp_path, make_tool(tmp_path)) == {}


def test_flags_modules_at_the_repo_root(tmp_path: Path) -> None:
    texts = {**make_tool(tmp_path), tmp_path / "script.py": "x = 1\n"}

    assert codes(tmp_path, texts) == {"script.py": ["CC301"]}


def test_modules_with_functions_need_a_mirrored_test(tmp_path: Path) -> None:
    texts = {
        **make_tool(tmp_path),
        tmp_path / "tool" / "scan.py": "def scan() -> None: ...\n",
        tmp_path / "tool" / "lang" / "__init__.py": "",
        tmp_path / "tool" / "lang" / "parse.py": "def parse() -> None: ...\n",
        tmp_path / "tool" / "tests" / "test_lang_parse.py": "",
        tmp_path / "tool" / "records.py": "class Record: ...\n",
    }

    assert codes(tmp_path, texts) == {"tool/scan.py": ["CC302"]}


def test_entry_module_must_keep_its_shape(tmp_path: Path) -> None:
    texts = make_tool(tmp_path)
    texts[tmp_path / "tool" / "__main__.py"] = (
        "import argparse\n\n\ndef main():\n    return 0\n\n\nmain()\n"
    )

    assert codes(tmp_path, texts) == {"tool/__main__.py": ["CC303", "CC303", "CC303"]}


def test_a_tool_needs_an_entry_module_and_errors(tmp_path: Path) -> None:
    texts = {tmp_path / "tool" / "__init__.py": ""}

    assert codes(tmp_path, texts) == {"tool/__init__.py": ["CC303", "CC304"]}


def test_tools_import_only_utils(tmp_path: Path) -> None:
    texts = {
        **make_tool(tmp_path, "first"),
        **make_tool(tmp_path, "second"),
        tmp_path / "utils" / "__init__.py": "",
        tmp_path
        / "first"
        / "share.py": "import utils\nfrom second.errors import ToolError\n",
    }

    assert codes(tmp_path, texts) == {"first/share.py": ["CC305"]}
