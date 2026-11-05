from pathlib import Path

from ..comments import space_comment
from ..findings import Cleaned, Finding
from ..settings import Settings


def clean_ignore(text: str, path: Path, settings: Settings) -> Cleaned:
    lines = [strip_trailing(line) for line in text.splitlines()]
    blocks = drop_repeats(split_blocks(lines))
    blocks = [[space_comment(line) for line in block] for block in blocks]

    if settings.ignore.sort_blocks:
        blocks = [sort_block(block) for block in blocks]

    cleaned = "\n\n".join("\n".join(block) for block in blocks)
    findings = find_headless_blocks(blocks) if settings.ignore.require_headers else []

    return Cleaned(text=cleaned + "\n" if cleaned else "", findings=tuple(findings))


def strip_trailing(line: str) -> str:
    stripped = line.rstrip()

    # "\ " at the end of a pattern is an escaped, meaningful space
    if stripped.endswith("\\") and len(stripped) < len(line):
        return stripped + " "

    return stripped


def split_blocks(lines: list[str]) -> list[list[str]]:
    blocks = []
    current = []

    for line in [*lines, ""]:
        if line:
            current.append(line)
            continue

        if current:
            blocks.append(current)
            current = []

    return blocks


def drop_repeats(blocks: list[list[str]]) -> list[list[str]]:
    seen = set[str]()
    kept = []

    for block in blocks:
        lines = []

        for line in block:
            is_pattern = not line.startswith("#")

            if is_pattern and line in seen:
                continue

            # a negation can re-include files, so a later repeat is meaningful again
            if line.startswith("!"):
                seen.clear()
            elif is_pattern:
                seen.add(line)

            lines.append(line)

        if lines:
            kept.append(lines)

    return kept


def sort_block(block: list[str]) -> list[str]:
    header_length = next(
        (index for index, line in enumerate(block) if not line.startswith("#")),
        len(block),
    )
    header, patterns = block[:header_length], block[header_length:]

    # with a negation or a comment among the patterns, their order carries meaning
    if any(line.startswith(("!", "#")) for line in patterns):
        return block

    return header + sorted(patterns)


def find_headless_blocks(blocks: list[list[str]]) -> list[Finding]:
    findings = []
    line = 1

    for block in blocks:
        if not block[0].startswith("#"):
            findings.append(
                Finding(
                    line=line,
                    column=1,
                    code="CC401",
                    message="start each block with a # comment naming what it ignores",
                    is_error=True,
                )
            )

        line += len(block) + 1

    return findings
