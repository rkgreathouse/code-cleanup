import configparser
import logging
import re
import tomllib
from pathlib import Path

log = logging.getLogger(__name__)

MINIMUM = re.compile(r"(?:>=|~=|==)\s*(\d+)\.(\d+)")


def find_minimum_python(root: Path) -> tuple[int, int] | None:
    sources = [
        ("pyproject.toml", read_pyproject),
        ("setup.cfg", read_setup_cfg),
        ("setup.py", read_setup_py),
    ]

    for name, read in sources:
        path = root / name

        if not path.is_file():
            continue

        # the project's own floor: rewriting to newer syntax would break its users
        if (version := parse_minimum(read(path))) is not None:
            log.debug("%s requires Python %d.%d", path, *version)
            return version

    return None


def read_pyproject(path: Path) -> str:
    try:
        data = tomllib.loads(path.read_text())

    except tomllib.TOMLDecodeError:
        return ""

    project = data.get("project")
    value = project.get("requires-python") if isinstance(project, dict) else None

    return value if isinstance(value, str) else ""


def read_setup_cfg(path: Path) -> str:
    parser = configparser.ConfigParser()

    try:
        parser.read_string(path.read_text())

    except configparser.Error:
        return ""

    return parser.get("options", "python_requires", fallback="")


def read_setup_py(path: Path) -> str:
    match = re.search(r"python_requires\s*=\s*[\"']([^\"']+)[\"']", path.read_text())
    return match.group(1) if match else ""


def parse_minimum(specifier: str) -> tuple[int, int] | None:
    match = MINIMUM.search(specifier)
    return (int(match.group(1)), int(match.group(2))) if match else None
