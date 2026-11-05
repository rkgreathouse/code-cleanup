from pathlib import Path

import pytest

from ..errors import MavenError
from ..java.maven import (
    cache_name,
    compiler_exports,
    find_module,
    group_by_module,
    parse_coordinate,
    resolve_tool,
)


def test_resolves_a_pinned_tool_to_a_classpath() -> None:
    classpath = resolve_tool("com.google.googlejavaformat:google-java-format:2.0.0")

    assert "google-java-format-2.0.0.jar" in classpath


def test_names_each_version_its_own_cache_folder() -> None:
    first = cache_name("g:tool:1.0")

    assert first.startswith("tool-")
    assert first != cache_name("g:tool:1.1")


def test_rejects_a_coordinate_without_a_version() -> None:
    with pytest.raises(MavenError, match="group:artifact:version"):
        parse_coordinate("g:tool")


def test_groups_files_by_their_nearest_pom(tmp_path: Path) -> None:
    (tmp_path / "pom.xml").write_text("")
    (tmp_path / "api" / "pom.xml").parent.mkdir()
    (tmp_path / "api" / "pom.xml").write_text("")
    top = tmp_path / "src" / "A.java"
    nested = tmp_path / "api" / "src" / "B.java"

    assert group_by_module(tmp_path, [top, nested]) == {
        tmp_path: [top],
        tmp_path / "api": [nested],
    }


def test_never_looks_above_the_scanned_root(tmp_path: Path) -> None:
    (tmp_path / "pom.xml").write_text("")
    root = tmp_path / "inner"

    assert find_module(root, root / "src" / "A.java") == root


def test_opens_the_compiler_to_tools_that_need_it() -> None:
    flags = compiler_exports("-J")

    assert "-J--add-exports=jdk.compiler/com.sun.tools.javac.api=ALL-UNNAMED" in flags
    assert all(flag.startswith("-J--add-") for flag in flags)
