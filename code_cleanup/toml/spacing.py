import re

from ..comments import space_comment

TABLE_HEADER = re.compile(r"\[\[?[\w.\"' -]+\]\]?\s*(#.*)?")


def space_tables(text: str) -> str:
    lines = text.splitlines(keepends=True)
    in_string = find_string_lines(lines)
    output = []

    for number, line in enumerate(lines):
        if in_string[number]:
            output.append(line)
            continue

        line = space_comment(line)

        # a header's own comments stay against it; the blank line goes above them
        if TABLE_HEADER.fullmatch(line.rstrip("\n")):
            insert_blank_line(output)

        output.append(line)

    return "".join(output)


def find_string_lines(lines: list[str]) -> list[bool]:
    flags = []
    delimiter = None

    for line in lines:
        flags.append(delimiter is not None)

        for match in re.finditer(r'"""|\'\'\'', line):
            if delimiter is None:
                delimiter = match.group()
            elif match.group() == delimiter:
                delimiter = None

    return flags


def insert_blank_line(output: list[str]) -> None:
    position = len(output)

    while position > 0 and output[position - 1].startswith("#"):
        position -= 1

    if position > 0 and output[position - 1].strip():
        output.insert(position, "\n")
