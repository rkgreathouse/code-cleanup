from collections.abc import Iterator

import tree_sitter_java
from tree_sitter import Language, Node, Parser, Tree

from ..findings import Finding

JAVA = Language(tree_sitter_java.language())


def parse_java(text: str) -> Tree:
    return Parser(JAVA).parse(text.encode())


def find_syntax_error(tree: Tree) -> Finding | None:
    if not tree.root_node.has_error:
        return None

    broken = next(
        (node for node in walk(tree.root_node) if node.is_error or node.is_missing),
        tree.root_node,
    )
    line, column = position(broken)
    detail = f"missing {broken.type}" if broken.is_missing else "unexpected code"

    return Finding(
        line=line,
        column=column,
        code="CC000",
        message=f"syntax error, file left as is: {detail}",
        is_error=True,
    )


def walk(node: Node) -> Iterator[Node]:
    yield node

    for child in node.children:
        yield from walk(child)


def text_of(node: Node | None) -> str:
    if node is None or node.text is None:
        return ""

    return node.text.decode()


def position(node: Node) -> tuple[int, int]:
    return node.start_point.row + 1, node.start_point.column + 1


def finding_at(node: Node, code: str, message: str, is_error: bool = True) -> Finding:
    line, column = position(node)
    return Finding(line, column, code, message, is_error)


def has_modifier(node: Node, keyword: str) -> bool:
    modifiers = next(
        (child for child in node.children if child.type == "modifiers"), None
    )

    if modifiers is None:
        return False

    return any(text_of(child) == keyword for child in modifiers.children)


def annotation_names(node: Node) -> set[str]:
    modifiers = next(
        (child for child in node.children if child.type == "modifiers"), None
    )

    if modifiers is None:
        return set()

    return {
        text_of(child.child_by_field_name("name"))
        for child in modifiers.children
        if child.type in ("annotation", "marker_annotation")
    }
