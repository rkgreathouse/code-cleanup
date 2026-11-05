import hashlib
import json
import subprocess
import sys
import sysconfig
import tempfile
from pathlib import Path

from ..errors import RuffError
from ..findings import Finding
from ..settings import PythonSettings


def fix_lint(text: str, path: Path, settings: PythonSettings) -> str:
    return run_ruff(["check", "--fix", "--exit-zero"], text, path, settings)


def format_code(text: str, path: Path, settings: PythonSettings) -> str:
    return run_ruff(["format"], text, path, settings)


def find_lint(text: str, path: Path, settings: PythonSettings) -> list[Finding]:
    output = run_ruff(
        ["check", "--exit-zero", "--output-format", "json"], text, path, settings
    )

    return [to_finding(entry) for entry in json.loads(output)]


def run_ruff(args: list[str], text: str, path: Path, settings: PythonSettings) -> str:
    config_path = write_ruff_config(settings.ruff_toml)
    command = [*find_ruff(), *args, "--config", str(config_path)]

    result = subprocess.run(
        [*command, "--stdin-filename", str(path.resolve()), "-"],
        input=text,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuffError(f"ruff {args[0]} failed on {path}: {result.stderr.strip()}")

    return result.stdout


def find_ruff() -> list[str]:
    name = "ruff.exe" if sys.platform == "win32" else "ruff"
    binary = Path(sysconfig.get_path("scripts")) / name

    # calling the binary skips a Python start-up per call; -m ruff finds it anywhere
    if binary.is_file():
        return [str(binary)]

    return [sys.executable, "-m", "ruff"]


def write_ruff_config(ruff_toml: str) -> Path:
    digest = hashlib.sha256(ruff_toml.encode()).hexdigest()[:16]
    path = Path(tempfile.gettempdir()) / "code-cleanup" / f"ruff-{digest}.toml"

    # named by content, so an existing file already holds exactly this style
    if path.is_file():
        return path

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(ruff_toml)

    except OSError as error:
        raise RuffError(f"could not write ruff config to {path}: {error}") from error

    return path


def to_finding(entry: dict[str, object]) -> Finding:
    location = entry.get("location")
    code = entry.get("code")
    row = location.get("row") if isinstance(location, dict) else None
    column = location.get("column") if isinstance(location, dict) else None

    return Finding(
        line=row if isinstance(row, int) else 1,
        column=column if isinstance(column, int) else 1,
        code=code if isinstance(code, str) else "syntax",
        message=str(entry.get("message", "")),
        is_error=True,
    )
