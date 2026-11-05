import shutil
import sys
import sysconfig
from pathlib import Path

from .errors import ToolNotFoundError


def find_tool(name: str) -> str:
    executable = f"{name}.exe" if sys.platform == "win32" else name
    installed = Path(sysconfig.get_path("scripts")) / executable

    # the copy installed beside this Python is the pinned one; PATH is the fallback
    if installed.is_file():
        return str(installed)

    found = shutil.which(name)

    if found is None:
        raise ToolNotFoundError(f"{name} is not installed; reinstall code-cleanup")

    return found
