import subprocess
from pathlib import Path

import pytest

from ..discover import find_files
from ..errors import DiscoveryError


def write(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x = 1\n")

    return path


def test_walks_every_file_outside_excluded_folders(tmp_path: Path) -> None:
    kept = write(tmp_path / "pkg" / "a.py")
    write(tmp_path / ".venv" / "lib" / "b.py")

    assert find_files(tmp_path, (".venv",)) == [kept]


def test_honours_gitignore_inside_a_work_tree(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text("generated/\n")
    kept = write(tmp_path / "a.py")
    write(tmp_path / "generated" / "b.py")

    assert find_files(tmp_path, ()) == [tmp_path / ".gitignore", kept]


def test_root_must_be_a_directory(tmp_path: Path) -> None:
    with pytest.raises(DiscoveryError, match="not a directory"):
        find_files(tmp_path / "missing", ())
