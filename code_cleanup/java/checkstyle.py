import hashlib
import subprocess
import tempfile
import xml.etree.ElementTree as ElementTree
from pathlib import Path

from ..errors import MavenError
from ..findings import Finding, group_by_path
from ..settings import JavaSettings
from .maven import find_jdk_tool, resolve_tool

CHECKSTYLE_MAIN = "com.puppycrawl.tools.checkstyle.Main"


def find_checkstyle_issues(
    mirror: Path, root: Path, paths: list[Path], settings: JavaSettings
) -> dict[Path, list[Finding]]:
    classpath = resolve_tool(settings.checkstyle)
    config = write_config(settings.checkstyle_xml)
    command = [find_jdk_tool("java"), "-cp", classpath, CHECKSTYLE_MAIN]
    command += ["-c", str(config), "-f", "xml"]
    relative_paths = [str(path.relative_to(root)) for path in paths]

    result = subprocess.run(
        [*command, *relative_paths],
        cwd=mirror,
        capture_output=True,
        text=True,
        check=False,
    )

    # Checkstyle exits with the number of violations; only a missing report is a failure
    if "<checkstyle" not in result.stdout:
        detail = result.stderr.strip().splitlines()
        message = detail[-1] if detail else "Checkstyle stopped without a message"
        return {root: [Finding(1, 1, "checkstyle", message, is_error=True)]}

    return group_by_file(result.stdout, mirror, root)


def write_config(checkstyle_xml: str) -> Path:
    digest = hashlib.sha256(checkstyle_xml.encode()).hexdigest()[:16]
    path = Path(tempfile.gettempdir()) / "code-cleanup" / f"checkstyle-{digest}.xml"

    # named by content, so an existing file already holds exactly this style
    if path.is_file():
        return path

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(checkstyle_xml)

    except OSError as error:
        raise MavenError(
            f"could not write checkstyle config to {path}: {error}"
        ) from error

    return path


def group_by_file(report: str, mirror: Path, root: Path) -> dict[Path, list[Finding]]:
    issues = []

    for file in ElementTree.fromstring(report).iter("file"):
        path = root / Path(file.get("name", "")).resolve().relative_to(mirror.resolve())
        issues += [(path, to_finding(error)) for error in file.iter("error")]

    return group_by_path(issues)


def to_finding(error: ElementTree.Element) -> Finding:
    source = error.get("source", "")
    check = source.rsplit(".", 1)[-1].removesuffix("Check")

    return Finding(
        line=int(error.get("line", "1")),
        column=int(error.get("column", "1")),
        code=f"checkstyle:{check}",
        message=error.get("message", ""),
        is_error=error.get("severity") == "error",
    )
