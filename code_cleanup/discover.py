import logging
import subprocess
from pathlib import Path

from .errors import DiscoveryError

log = logging.getLogger(__name__)


def find_files(root: Path, exclude: tuple[str, ...]) -> list[Path]:
    if not root.is_dir():
        raise DiscoveryError(f"not a directory: {root}")

    candidates = list_git_files(root)

    # outside a git work tree there is no .gitignore to honour, so walk everything
    if candidates is None:
        candidates = list_all_files(root)

    return sorted(
        path
        for path in candidates
        if path.is_file() and not is_excluded(path.relative_to(root), exclude)
    )


def list_git_files(root: Path) -> list[Path] | None:
    command = ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others"]

    try:
        result = subprocess.run(
            [*command, "--exclude-standard"], capture_output=True, check=False
        )

    except FileNotFoundError:
        log.debug("git not found; walking %s", root)
        return None

    if result.returncode != 0:
        log.debug("%s is not in a git work tree; walking it", root)
        return None

    names = result.stdout.decode().split("\0")

    return [root / name for name in names if name]


def list_all_files(root: Path) -> list[Path]:
    return [path for path in root.rglob("*") if path.is_file()]


def is_excluded(relative_path: Path, exclude: tuple[str, ...]) -> bool:
    return any(part in exclude for part in relative_path.parts)
