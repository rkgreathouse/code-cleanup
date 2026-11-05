from ..java.syntax import (
    annotation_names,
    find_syntax_error,
    has_modifier,
    parse_java,
    text_of,
)


def test_finds_no_error_in_valid_code() -> None:
    assert find_syntax_error(parse_java("class A { void f() {} }\n")) is None


def test_points_at_the_broken_code() -> None:
    error = find_syntax_error(parse_java("class A {\n  void f( {\n}\n"))

    assert error is not None
    assert (error.code, error.line) == ("CC000", 2)


def test_reads_modifiers_and_annotations() -> None:
    tree = parse_java("@Service @Deprecated public final class A {}\n")
    node = tree.root_node.named_children[0]

    assert annotation_names(node) == {"Service", "Deprecated"}
    assert has_modifier(node, "final")
    assert not has_modifier(node, "static")
    assert text_of(node.child_by_field_name("name")) == "A"
