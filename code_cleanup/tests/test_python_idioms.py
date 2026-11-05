import ast
from dataclasses import replace

from ..python.idioms import find_idiom_issues
from .test_python_spacing import make_settings


def codes(source: str) -> list[str]:
    findings = find_idiom_issues(ast.parse(source), make_settings())
    return [finding.code for finding in findings]


def test_allows_one_for_and_one_if() -> None:
    assert codes("names = [n.upper() for n in names if n]\n") == []


def test_flags_two_fors_two_ifs_or_nesting() -> None:
    assert codes("pairs = [(a, b) for a in x for b in y]\n") == ["CC105"]
    assert codes("odd = [n for n in x if n if n % 2]\n") == ["CC105"]
    assert codes("rows = [[c for c in row] for row in grid]\n") == ["CC105"]


def test_suggests_walrus_for_a_value_only_tested_once() -> None:
    source = (
        "def f(line):\n"
        "    match = pattern.search(line)\n"
        "    if match is None:\n"
        "        return ''\n"
        "    return 'x'\n"
    )

    assert codes(source) == ["CC106"]


def test_keeps_values_used_after_the_if() -> None:
    source = (
        "def f(line):\n"
        "    match = pattern.search(line)\n"
        "    if match is None:\n"
        "        return ''\n"
        "    return match.group()\n"
    )

    assert codes(source) == []


def test_keeps_named_conditions() -> None:
    source = (
        "def f(token):\n"
        "    is_comment = token.type == COMMENT\n"
        "    if is_comment and token.line:\n"
        "        return 1\n"
        "    return 0\n"
    )

    assert codes(source) == []


def test_walrus_suggestions_are_warnings_and_can_be_off() -> None:
    source = (
        "def f():\n    value = g()\n    if value:\n        return 1\n    return 0\n"
    )
    findings = find_idiom_issues(ast.parse(source), make_settings())
    quiet = replace(make_settings(), suggest_walrus=False)

    assert [finding.is_error for finding in findings] == [False]
    assert find_idiom_issues(ast.parse(source), quiet) == []
