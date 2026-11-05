def apply_spacing(
    lines: list[str], blank_before: set[int], tight_before: set[int]
) -> str:
    dropped = find_blanks_before(lines, tight_before)
    output = []
    previous = ""

    for number, line in enumerate(lines, start=1):
        if number in dropped:
            continue

        if number in blank_before and previous.strip():
            output.append("\n")

        output.append(line)
        previous = line

    return "".join(output)


def find_blanks_before(lines: list[str], line_numbers: set[int]) -> set[int]:
    blanks = set()

    for number in line_numbers:
        above = number - 1

        while above >= 1 and not lines[above - 1].strip():
            blanks.add(above)
            above -= 1

    return blanks
