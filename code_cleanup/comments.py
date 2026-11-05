def space_comment(line: str) -> str:
    if line.startswith("#") and len(line) > 1 and line[1].isalnum():
        return "# " + line[1:]

    return line
