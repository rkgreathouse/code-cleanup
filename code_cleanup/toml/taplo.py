import subprocess
from pathlib import Path

from ..errors import TaploError
from ..settings import TomlSettings
from ..tools import find_tool


def format_toml(text: str, path: Path, settings: TomlSettings) -> str:
    options = []

    for option in settings.taplo_options:
        options += ["-o", option]

    command = [find_tool("taplo"), "format", "--no-auto-config", *options, "-"]

    result = subprocess.run(
        command, input=text, capture_output=True, text=True, check=False
    )

    if result.returncode != 0:
        raise TaploError(f"taplo failed on {path}: {result.stderr.strip()}")

    return result.stdout
