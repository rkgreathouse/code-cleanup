from dataclasses import replace
from pathlib import Path

from ..java.spacing import space_blocks
from ..settings import load_settings

BEFORE = """class A {
  int f(int x) {

    int y = 1;
    if (x > 1) {
      // only large inputs
      if (y > 2) {
        return 1;
      }
      y++;
    } else {
      y--;
    }
    try {
      y++;
    } catch (RuntimeException e) {
      y--;
    } finally {
      y = 0;
    }
    return y; // done
  }
}
"""

AFTER = """class A {
  int f(int x) {
    int y = 1;

    if (x > 1) {

      // only large inputs
      if (y > 2) {
        return 1;
      }

      y++;
    } else {
      y--;
    }

    try {
      y++;

    } catch (RuntimeException e) {
      y--;

    } finally {
      y = 0;
    }

    return y; // done
  }
}
"""


def test_spaces_blocks_the_way_the_python_style_does(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None).java

    assert space_blocks(BEFORE, settings) == AFTER


def test_is_stable_on_its_own_output(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None).java

    assert space_blocks(AFTER, settings) == AFTER


def test_keeps_an_else_tight_against_its_if(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None).java
    source = (
        "class A {\n  void f() {\n    if (a) {\n      g();\n\n"
        "    } else {\n      h();\n    }\n  }\n}\n"
    )

    assert "g();\n    } else" in space_blocks(source, settings)


def test_leaves_a_try_without_catch_closing_tight(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None).java
    source = (
        "class A {\n  void f() {\n    try (var r = open()) {\n      g();\n"
        "    }\n  }\n}\n"
    )

    assert space_blocks(source, settings) == source


def test_switches_turn_rules_off(tmp_path: Path) -> None:
    settings = replace(
        load_settings(tmp_path, None).java,
        blank_lines_around_blocks=False,
        blank_line_before_block_comment=False,
        blank_line_before_catch=False,
    )
    source = (
        "class A {\n  void f() {\n    g();\n    if (a) {\n      h();\n    }\n  }\n}\n"
    )

    assert space_blocks(source, settings) == source
