from dataclasses import replace
from pathlib import Path

from ..java.checks import find_style_issues
from ..java.syntax import parse_java
from ..settings import load_settings


def codes(source: str, tmp_path: Path) -> list[str]:
    settings = load_settings(tmp_path, None).java
    return [finding.code for finding in find_style_issues(parse_java(source), settings)]


def test_reports_javadoc_but_not_plain_comments(tmp_path: Path) -> None:
    source = "/** Doc. */\nclass A {\n  /* note */\n  // note\n}\n"

    assert codes(source, tmp_path) == ["CC103"]


def test_reports_environment_and_value_reads(tmp_path: Path) -> None:
    source = (
        "class A {\n"
        '  @Value("${a}") int a;\n'
        '  String f() { return System.getenv("HOME") + System.getProperty("x"); }\n'
        "}\n"
    )

    assert codes(source, tmp_path) == ["CC104", "CC104", "CC104"]


def test_allows_two_constants_per_file(tmp_path: Path) -> None:
    source = (
        "class A {\n"
        "  static final int A = 1;\n"
        "  static final int B = 2;\n"
        "  private static final Logger log = null;\n"
        "  static final int C = 3;\n"
        "}\n"
    )

    assert codes(source, tmp_path) == ["CC102"]


def test_keeps_streams_to_one_map_and_one_filter(tmp_path: Path) -> None:
    simple = (
        "class A { Object f() { return xs.stream().filter(a).map(b).toList(); } }\n"
    )
    tangled = "class A { Object f() { return xs.stream().map(a).map(b).toList(); } }\n"
    flat = "class A { Object f() { return xs.stream().flatMap(a).toList(); } }\n"
    nested = (
        "class A { Object f() { return xs.stream()"
        ".map(x -> x.ys().stream().count()).toList(); } }\n"
    )

    assert codes(simple, tmp_path) == []
    assert codes(tangled, tmp_path) == ["CC105"]
    assert codes(flat, tmp_path) == ["CC105"]
    assert codes(nested, tmp_path) == ["CC105"]


def test_leaves_optional_chains_alone(tmp_path: Path) -> None:
    source = "class A { Object f() { return o.map(a).map(b).orElse(c); } }\n"

    assert codes(source, tmp_path) == []


def test_reports_nesting_past_four_blocks_once(tmp_path: Path) -> None:
    source = (
        "class A { void f() {\n"
        "  for (;;) { if (a) { while (b) { try { if (c) { if (d) { g(); } } }"
        " finally { h(); } } } }\n"
        "} }\n"
    )

    assert codes(source, tmp_path) == ["CC107"]


def test_counts_else_if_as_one_level(tmp_path: Path) -> None:
    source = (
        "class A { void f() {\n"
        "  for (;;) { while (b) { if (a) { g(); } else if (b) { if (c) { h(); } } } }\n"
        "} }\n"
    )

    assert codes(source, tmp_path) == []


def test_switches_turn_checks_off(tmp_path: Path) -> None:
    settings = replace(
        load_settings(tmp_path, None).java,
        allow_javadoc=True,
        allow_environment=True,
        simple_streams=False,
    )
    source = '/** Doc. */\nclass A { String f() { return System.getenv("A"); } }\n'

    assert find_style_issues(parse_java(source), settings) == []
