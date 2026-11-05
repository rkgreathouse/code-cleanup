from pathlib import Path

from ..java.clean import check_java_project, clean_java
from ..settings import load_settings


def test_formats_spaces_and_checks_a_file(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None)
    source = "/** Doc. */\nclass A{int f(int x){int y=1;if(x>1){y++;}return y;}}\n"

    cleaned = clean_java(source, tmp_path / "A.java", settings)

    assert cleaned.text == (
        "/** Doc. */\nclass A {\n  int f(int x) {\n    int y = 1;\n\n"
        "    if (x > 1) {\n      y++;\n    }\n\n    return y;\n  }\n}\n"
    )
    assert [finding.code for finding in cleaned.findings] == ["CC103"]


def test_leaves_a_file_that_does_not_parse(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None)
    source = "class A { void f( }\n"

    cleaned = clean_java(source, tmp_path / "A.java", settings)

    assert cleaned.text == source
    assert [finding.code for finding in cleaned.findings] == ["CC000"]


def test_checks_the_project_without_writing_into_it(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None)
    path = tmp_path / "A.java"
    texts = {path: "class A {\n  void f() {\n    System.out.println(1);\n  }\n}\n"}

    findings = check_java_project(tmp_path, texts, settings)

    assert [finding.code for finding in findings[path]] == ["checkstyle:Regexp"]
    assert list(tmp_path.iterdir()) == []


def test_skips_the_project_pass_for_files_that_do_not_parse(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None)

    assert (
        check_java_project(tmp_path, {tmp_path / "A.java": "class {"}, settings) == {}
    )
