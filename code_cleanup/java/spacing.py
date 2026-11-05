from tree_sitter import Node

from ..blank_lines import apply_spacing
from ..settings import JavaSettings
from .syntax import parse_java, walk

BLOCKS = {
    "if_statement",
    "for_statement",
    "enhanced_for_statement",
    "while_statement",
    "do_statement",
    "try_statement",
    "try_with_resources_statement",
    "switch_expression",
    "synchronized_statement",
    "labeled_statement",
}
COMMENTS = {"line_comment", "block_comment"}


def space_blocks(text: str, settings: JavaSettings) -> str:
    tree = parse_java(text)
    blank_before = set()
    tight_before = set()

    for node in walk(tree.root_node):
        if node.type in ("block", "constructor_body", "switch_block_statement_group"):
            gaps, tight = find_block_gaps(statements_of(node), settings)
            blank_before |= gaps
            tight_before |= tight

        if node.type in ("try_statement", "try_with_resources_statement"):
            blank_before |= find_catch_lines(node, settings)

        if node.type == "if_statement":
            tight_before |= find_else_lines(node)

    return apply_spacing(text.splitlines(keepends=True), blank_before, tight_before)


def statements_of(body: Node) -> list[tuple[int, Node]]:
    statements = []
    comment_start = None
    previous_end = -1

    for child in body.named_children:

        # a comment after code on the same line belongs to that code
        if child.type in COMMENTS and child.start_point.row == previous_end:
            continue

        if child.type in COMMENTS:
            comment_start = (
                child.start_point.row if comment_start is None else comment_start
            )
            continue

        if child.type == "switch_label":
            continue

        start = child.start_point.row if comment_start is None else comment_start
        statements.append((start + 1, child))
        comment_start = None
        previous_end = child.end_point.row

    return statements


def find_block_gaps(
    statements: list[tuple[int, Node]], settings: JavaSettings
) -> tuple[set[int], set[int]]:
    gaps = set()
    tight = set()

    for index, (start, statement) in enumerate(statements):
        is_block = statement.type in BLOCKS
        follows_block = index > 0 and statements[index - 1][1].type in BLOCKS
        has_comment = start <= statement.start_point.row
        keeps_opening_gap = (
            is_block and has_comment and settings.blank_line_before_block_comment
        )

        if (
            index > 0
            and settings.blank_lines_around_blocks
            and (is_block or follows_block)
        ):
            gaps.add(start)

        # a comment that opens a block reads as the reason for it, set apart like one
        if index == 0 and keeps_opening_gap:
            gaps.add(start)

        if index == 0 and not keeps_opening_gap:
            tight.add(start)

    return gaps, tight


def find_catch_lines(node: Node, settings: JavaSettings) -> set[int]:
    if not settings.blank_line_before_catch:
        return set()

    bodies = [
        child.child_by_field_name("body") if child.type == "catch_clause" else child
        for child in node.named_children
        if child.type in ("block", "catch_clause")
    ]

    # the last body ends the statement; each other one ends before a catch or finally
    if not has_finally(node):
        bodies = bodies[:-1]

    return {
        body.end_point.row + 1
        for body in bodies
        if body is not None and body.named_child_count and closes_own_line(body)
    }


def has_finally(node: Node) -> bool:
    return any(child.type == "finally_clause" for child in node.named_children)


def closes_own_line(body: Node) -> bool:
    return body.end_point.row > body.start_point.row


def find_else_lines(node: Node) -> set[int]:
    consequence = node.child_by_field_name("consequence")

    if node.child_by_field_name("alternative") is None or consequence is None:
        return set()

    return {consequence.end_point.row + 1}
