import subprocess
from pathlib import Path

from ..findings import Finding
from ..settings import JavaSettings
from .maven import compiler_exports, find_jdk_tool, resolve_tool

FORMATTER_MAIN = "com.google.googlejavaformat.java.Main"


def format_java(text: str, path: Path, settings: JavaSettings) -> str | Finding:
    classpath = resolve_tool(settings.formatter)
    command = [find_jdk_tool("java"), *compiler_exports(""), "-cp", classpath]

    result = subprocess.run(
        [*command, FORMATTER_MAIN, "-"],
        input=text,
        capture_output=True,
        text=True,
        check=False,
    )

    # google-java-format rejects code javac would reject; the file is left as is
    if result.returncode != 0:
        return to_finding(result.stderr, path)

    return result.stdout


def to_finding(stderr: str, path: Path) -> Finding:
    lines = [line for line in stderr.splitlines() if not line.startswith("Picked up")]
    first = lines[0] if lines else "google-java-format failed"
    location, _, message = first.partition(": error: ")
    parts = location.rsplit(":", 2)

    # errors read "<stdin>:LINE:COLUMN: error: message"
    if message and len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
        return Finding(
            int(parts[1]), int(parts[2]), "CC000", f"{message}; file left as is", True
        )

    return Finding(1, 1, "CC000", f"{path.name}: {first}; file left as is", True)
