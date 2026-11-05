from ..toml.spacing import space_tables


def test_puts_a_blank_line_above_each_table_and_its_comments() -> None:
    text = "[a]\nx = 1\n#about b\n[b]\ny = 2\n[[c]]\nz = 3\n"

    assert space_tables(text) == (
        "[a]\nx = 1\n\n# about b\n[b]\ny = 2\n\n[[c]]\nz = 3\n"
    )


def test_leaves_arrays_of_arrays_alone() -> None:
    text = "matrix = [\n    [1, 2],\n    [3, 4],\n]\n"

    assert space_tables(text) == text


def test_leaves_multi_line_strings_alone() -> None:
    text = 'notes = """\n#raw\n[not.a.table]\n"""\n'

    assert space_tables(text) == text


def test_is_idempotent() -> None:
    once = space_tables("[a]\nx = 1\n[b]\n")

    assert space_tables(once) == once
