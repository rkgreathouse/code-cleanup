import ast
import io
import tokenize

from ..blank_lines import apply_spacing
from ..settings import PythonSettings

BLOCKS = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.With,
    ast.AsyncWith,
    ast.Try,
    ast.TryStar,
    ast.Match,
)
DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def space_blocks(text: str, settings: PythonSettings) -> str:
    tree = ast.parse(text)
    lines = text.splitlines(keepends=True)
    comment_lines = find_comment_lines(text)
    blank_before = set()
    tight_before = set()

    for node in ast.walk(tree):
        for body in statement_bodies(node, lines):
            blank_before |= find_block_gaps(body, lines, comment_lines, settings)

        if (
            isinstance(node, ast.Try | ast.TryStar)
            and settings.blank_line_before_except
        ):
            blank_before |= find_handler_lines(node, lines, comment_lines)

        if isinstance(node, ast.If) and settings.tight_else:
            tight_before |= find_else_lines(node, lines)

    return apply_spacing(lines, blank_before, tight_before)


def find_comment_lines(text: str) -> set[int]:
    comment_lines = set()

    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        is_own_line = token.line[: token.start[1]].strip() == ""

        if token.type == tokenize.COMMENT and is_own_line:
            comment_lines.add(token.start[0])

    return comment_lines


def statement_bodies(node: ast.AST, lines: list[str]) -> list[list[ast.stmt]]:
    bodies = []

    for field in ("body", "orelse", "finalbody"):
        body = getattr(node, field, None)

        # an elif is the If's orelse, but it is a clause of this If, not a new block
        if field == "orelse" and isinstance(node, ast.If) and is_elif(body, lines):
            continue

        if isinstance(body, list) and body and isinstance(body[0], ast.stmt):
            bodies.append(body)

    return bodies


def is_elif(body: object, lines: list[str]) -> bool:
    if not isinstance(body, list) or len(body) != 1 or not isinstance(body[0], ast.If):
        return False

    return lines[body[0].lineno - 1].lstrip().startswith("elif")


def find_block_gaps(
    body: list[ast.stmt],
    lines: list[str],
    comment_lines: set[int],
    settings: PythonSettings,
) -> set[int]:
    gaps = set()

    for index, statement in enumerate(body):
        start = leading_comment_line(
            first_line(statement), statement.col_offset, comment_lines, lines
        )
        is_block = isinstance(statement, BLOCKS)
        opens_body = index == 0 or (index == 1 and is_docstring(body[0]))
        follows_block = index > 0 and isinstance(body[index - 1], BLOCKS)
        has_comment = start < first_line(statement)

        if (
            not opens_body
            and settings.blank_lines_around_blocks
            and (is_block or follows_block)
        ):
            gaps.add(start)

        # ruff format deletes a blank line that opens a block; a comment there keeps one
        if (
            opens_body
            and is_block
            and has_comment
            and settings.blank_line_before_block_comment
        ):
            gaps.add(start)

    return gaps


def is_docstring(statement: ast.stmt) -> bool:
    return (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Constant)
        and isinstance(statement.value.value, str)
    )


def find_handler_lines(
    node: ast.Try | ast.TryStar, lines: list[str], comment_lines: set[int]
) -> set[int]:
    clause_lines = {handler.lineno for handler in node.handlers}

    if node.finalbody:
        clause_lines.add(
            find_clause_line(lines, node.finalbody[0].lineno, node.col_offset)
        )

    return {
        leading_comment_line(line, node.col_offset, comment_lines, lines)
        for line in clause_lines
    }


def find_else_lines(node: ast.If, lines: list[str]) -> set[int]:
    if not node.orelse:
        return set()

    if is_elif(node.orelse, lines):
        return {node.orelse[0].lineno}

    return {find_clause_line(lines, node.orelse[0].lineno, node.col_offset)}


def find_clause_line(lines: list[str], body_line: int, column: int) -> int:
    line = body_line

    # the clause keyword is the nearest line above its body at the statement's indent
    while line > 1 and not is_at_indent(lines[line - 1], column):
        line -= 1

    return line


def first_line(statement: ast.stmt) -> int:
    if isinstance(statement, DEFINITIONS) and statement.decorator_list:
        return statement.decorator_list[0].lineno

    return statement.lineno


def leading_comment_line(
    line: int, column: int, comment_lines: set[int], lines: list[str]
) -> int:
    while line - 1 in comment_lines and indent(lines[line - 2]) == column:
        line -= 1

    return line


def indent(line: str) -> int:
    return len(line) - len(line.lstrip(" \t"))


def is_at_indent(line: str, column: int) -> bool:
    return bool(line.strip()) and indent(line) == column
