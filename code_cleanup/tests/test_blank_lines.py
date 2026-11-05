from ..blank_lines import apply_spacing


def test_adds_one_blank_line_before_a_marked_line() -> None:
    lines = ["a\n", "b\n", "c\n"]

    assert apply_spacing(lines, {2}, set()) == "a\n\nb\nc\n"


def test_does_not_double_an_existing_blank_line() -> None:
    lines = ["a\n", "\n", "b\n"]

    assert apply_spacing(lines, {3}, set()) == "a\n\nb\n"


def test_drops_every_blank_line_above_a_tight_line() -> None:
    lines = ["a\n", "\n", "\n", "b\n"]

    assert apply_spacing(lines, set(), {4}) == "a\nb\n"
