from dataclasses import replace
from pathlib import Path

from ..java.errorprone import find_bug_patterns, find_caret, group_by_file
from ..java.maven import tool_pom
from ..settings import load_settings

BUG = """package a;

class A {
  boolean same(String left, String right) {
    return left == right;
  }

  void trim(String text) {
    text.trim();
  }
}
"""


def write_project(tmp_path: Path) -> Path:
    path = tmp_path / "src" / "main" / "java" / "a" / "A.java"
    path.parent.mkdir(parents=True)
    path.write_text(BUG)
    (tmp_path / "pom.xml").write_text(tool_pom("org.slf4j:slf4j-api:2.0.17"))
    return path


def test_reports_bug_patterns_with_their_severity(tmp_path: Path) -> None:
    path = write_project(tmp_path)
    settings = load_settings(tmp_path, None).java

    findings = find_bug_patterns(tmp_path, tmp_path, [path], settings)

    assert [(item.code, item.line, item.is_error) for item in findings[path]] == [
        ("errorprone:ReferenceEquality", 5, False),
        ("errorprone:ReturnValueIgnored", 9, True),
    ]


def test_reports_a_module_without_a_pom(tmp_path: Path) -> None:
    path = tmp_path / "A.java"
    path.write_text(BUG)
    settings = load_settings(tmp_path, None).java

    findings = find_bug_patterns(tmp_path, tmp_path, [path], settings)

    assert [(item.code, item.is_error) for item in findings[tmp_path]] == [
        ("errorprone", False)
    ]


def test_can_be_switched_off(tmp_path: Path) -> None:
    path = write_project(tmp_path)
    settings = replace(load_settings(tmp_path, None).java, error_prone_enabled=False)

    assert find_bug_patterns(tmp_path, tmp_path, [path], settings) == {}


def test_reads_plain_compiler_errors_too() -> None:
    output = "src/A.java:4: error: cannot find symbol\n    Foo x;\n    ^\n"

    findings = group_by_file(output, Path("/project"))

    assert [
        (item.code, item.line, item.column)
        for item in findings[Path("/project/src/A.java")]
    ] == [("javac", 4, 5)]


def test_takes_the_column_from_the_caret_line() -> None:
    assert find_caret(["    return a == b;", "             ^"]) == 14
    assert find_caret(["  (see https://errorprone.info)"]) == 1
