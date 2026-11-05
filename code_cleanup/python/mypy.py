import json
import subprocess
import sys
import tempfile
from pathlib import Path

from ..findings import Finding
from ..settings import PythonSettings


def find_type_errors(
    root: Path, texts: dict[Path, str], settings: PythonSettings
) -> dict[Path, list[Finding]]:
    if not settings.mypy_enabled or not texts:
        return {}

    with tempfile.TemporaryDirectory(prefix="code-cleanup-") as mirror_name:
        mirror = Path(mirror_name)
        write_mirror(mirror, root, texts, settings.mypy_ini)
        result = run_mypy(mirror, root, sorted(texts))

    # exit 2 is a blocking error (duplicate module names, bad config): one finding
    if result.returncode > 1:
        detail = (result.stderr or result.stdout).strip().splitlines()
        message = detail[0] if detail else "mypy stopped without a message"
        return {root: [Finding(1, 1, "mypy", message, is_error=True)]}

    return group_by_file(result.stdout, root)


def write_mirror(mirror: Path, root: Path, texts: dict[Path, str], ini: str) -> None:
    (mirror / "mypy.ini").write_text(ini)

    for path, text in texts.items():
        copy = mirror / path.relative_to(root)
        copy.parent.mkdir(parents=True, exist_ok=True)
        copy.write_text(text)


def run_mypy(
    mirror: Path, root: Path, paths: list[Path]
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, "-m", "mypy", "--config-file", "mypy.ini"]
    command += ["--output", "json", "--cache-dir", ".mypy_cache"]
    project_python = root.resolve() / ".venv" / "bin" / "python"

    # the project's own environment holds its third-party packages and their stubs
    if project_python.is_file():
        command += ["--python-executable", str(project_python)]

    relative_paths = [str(path.relative_to(root)) for path in paths]
    return subprocess.run(
        [*command, *relative_paths],
        cwd=mirror,
        capture_output=True,
        text=True,
        check=False,
    )


def group_by_file(output: str, root: Path) -> dict[Path, list[Finding]]:
    # mypy also prints a plain-text summary line alongside the JSON lines
    entries = [json.loads(line) for line in output.splitlines() if line.startswith("{")]

    # notes only elaborate on the error before them
    errors = [entry for entry in entries if entry.get("severity") == "error"]
    paths = {root / entry["file"] for entry in errors}

    return {
        path: [to_finding(entry) for entry in errors if root / entry["file"] == path]
        for path in paths
    }


def to_finding(entry: dict[str, object]) -> Finding:
    line = entry.get("line")
    column = entry.get("column")
    code = entry.get("code")

    return Finding(
        line=line if isinstance(line, int) else 1,
        column=column + 1 if isinstance(column, int) else 1,
        code=f"mypy:{code}" if isinstance(code, str) else "mypy",
        message=str(entry.get("message", "")),
        is_error=True,
    )
