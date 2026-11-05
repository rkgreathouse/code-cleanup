from dataclasses import replace

from ..python.spacing import space_blocks
from ..settings import PythonSettings


def make_settings() -> PythonSettings:
    return PythonSettings(
        ruff_toml="",
        mypy_enabled=False,
        mypy_ini="",
        blank_lines_around_blocks=True,
        blank_line_before_block_comment=True,
        blank_line_before_except=True,
        tight_else=True,
        relative_imports=True,
        allow_docstrings=False,
        allow_environment=False,
        max_module_constants=2,
        logging_checks=True,
        log_format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        log_datefmt="%Y-%m-%d %H:%M:%S",
    )


def test_separates_blocks_from_their_neighbours() -> None:
    source = "def f(x):\n    y = 1\n    if x:\n        y = 2\n    return y\n"

    assert space_blocks(source, make_settings()) == (
        "def f(x):\n    y = 1\n\n    if x:\n        y = 2\n\n    return y\n"
    )


def test_leaves_a_block_that_opens_its_parent_block_tight() -> None:
    source = "for a in b:\n    for c in a:\n        print(c)\n"

    assert space_blocks(source, make_settings()) == source


def test_puts_the_blank_line_above_a_comment_that_opens_a_block() -> None:
    source = "for a in b:\n    # skip empties\n    if not a:\n        continue\n"

    assert space_blocks(source, make_settings()) == (
        "for a in b:\n\n    # skip empties\n    if not a:\n        continue\n"
    )


def test_keeps_comments_attached_to_the_block_they_explain() -> None:
    source = "x = 1\n# reason\nif x:\n    pass\n"

    assert (
        space_blocks(source, make_settings()) == "x = 1\n\n# reason\nif x:\n    pass\n"
    )


def test_separates_try_body_from_except_and_finally() -> None:
    source = "try:\n    a()\nexcept E:\n    b()\nfinally:\n    c()\n"

    assert space_blocks(source, make_settings()) == (
        "try:\n    a()\n\nexcept E:\n    b()\n\nfinally:\n    c()\n"
    )


def test_pulls_elif_and_else_against_the_if_body() -> None:
    source = "if a:\n    x()\n\nelif b:\n    y()\n\nelse:\n    z()\n"

    assert space_blocks(source, make_settings()) == (
        "if a:\n    x()\nelif b:\n    y()\nelse:\n    z()\n"
    )


def test_does_not_touch_lines_inside_strings() -> None:
    source = 'x = """\n# not a comment\nif y:\n"""\n'

    assert space_blocks(source, make_settings()) == source


def test_each_rule_can_be_switched_off() -> None:
    source = "x = 1\nif x:\n    pass\n"
    settings = replace(make_settings(), blank_lines_around_blocks=False)

    assert space_blocks(source, settings) == source


def test_is_idempotent() -> None:
    source = (
        "def f():\n    a = 1\n    while a:\n"
        "        # stop\n        if a:\n            break\n    return a\n"
    )
    once = space_blocks(source, make_settings())

    assert space_blocks(once, make_settings()) == once


def test_treats_a_docstring_as_part_of_the_header() -> None:
    source = 'def f(x):\n    """Doc."""\n    if x:\n        pass\n'

    assert space_blocks(source, make_settings()) == source
