from pathlib import Path

from ..findings import Finding
from ..java.format import format_java, to_finding
from ..settings import load_settings


def test_formats_to_google_style(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None).java

    formatted = format_java("class A{int f(){return 1;}}", Path("A.java"), settings)

    assert formatted == "class A {\n  int f() {\n    return 1;\n  }\n}\n"


def test_turns_a_compile_error_into_a_finding(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None).java

    formatted = format_java("class A{int f(){return 1}}", Path("A.java"), settings)

    assert isinstance(formatted, Finding)
    assert (formatted.code, formatted.line, formatted.column) == ("CC000", 1, 25)


def test_keeps_an_unexpected_message_whole() -> None:
    finding = to_finding("Picked up JAVA_TOOL_OPTIONS\nout of memory\n", Path("A.java"))

    assert finding.message == "A.java: out of memory; file left as is"
