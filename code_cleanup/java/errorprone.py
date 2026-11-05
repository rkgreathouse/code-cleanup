import logging
import re
import subprocess
import tempfile
from pathlib import Path

from ..findings import Finding, group_by_path
from ..settings import JavaSettings
from .maven import (
    compiler_exports,
    find_jdk_tool,
    group_by_module,
    resolve_project,
    resolve_tool,
)

log = logging.getLogger(__name__)

DIAGNOSTIC = re.compile(
    r"^(?P<path>.+?\.java):(?P<line>\d+): (?P<kind>error|warning): (?P<message>.*)$"
)


def find_bug_patterns(
    mirror: Path, root: Path, paths: list[Path], settings: JavaSettings
) -> dict[Path, list[Finding]]:
    if not settings.error_prone_enabled:
        return {}

    findings = dict[Path, list[Finding]]()

    for module, sources in group_by_module(root, paths).items():
        findings |= check_module(mirror, root, module, sources, settings)

    return findings


def check_module(
    mirror: Path, root: Path, module: Path, sources: list[Path], settings: JavaSettings
) -> dict[Path, list[Finding]]:
    if not (module / "pom.xml").is_file():
        message = "no pom.xml; Error Prone needs Maven to find the classpath"
        return {module: [Finding(1, 1, "errorprone", message, is_error=False)]}

    with tempfile.TemporaryDirectory(prefix="code-cleanup-") as scratch_name:
        scratch = Path(scratch_name)
        classpath = resolve_project(module, scratch / "classpath.txt")

        if classpath is None:
            message = "mvn dependency:build-classpath failed; Error Prone did not run"
            return {module / "pom.xml": [Finding(1, 1, "errorprone", message, True)]}

        log.debug("running Error Prone over %d files in %s", len(sources), module)
        result = run_javac(mirror, root, sources, classpath, scratch, settings)

    return group_by_file(result.stderr, root)


def run_javac(
    mirror: Path,
    root: Path,
    sources: list[Path],
    classpath: str,
    scratch: Path,
    settings: JavaSettings,
) -> subprocess.CompletedProcess[str]:
    plugin = " ".join(["ErrorProne", *settings.error_prone_flags])
    command = [find_jdk_tool("javac"), *compiler_exports("-J")]
    command += ["-XDcompilePolicy=simple", "-XDaddTypeAnnotationsToSymbol=true"]
    command += ["--should-stop=ifError=FLOW", "-proc:none"]
    command += ["-Xmaxerrs", "10000", "-Xmaxwarns", "10000"]
    command += ["--release", str(settings.release), "-d", str(scratch / "classes")]
    command += ["-processorpath", resolve_tool(settings.error_prone)]
    command += [f"-Xplugin:{plugin}", "-cp", classpath]
    relative_paths = [str(path.relative_to(root)) for path in sources]

    return subprocess.run(
        [*command, *relative_paths],
        cwd=mirror,
        capture_output=True,
        text=True,
        check=False,
    )


def group_by_file(output: str, root: Path) -> dict[Path, list[Finding]]:
    lines = output.splitlines()
    issues = []

    for index, line in enumerate(lines):
        if (match := DIAGNOSTIC.match(line)) is None:
            continue

        # javac was given paths relative to the mirror, and reports them the same way
        column = find_caret(lines[index + 1 : index + 4])
        issues.append((root / match["path"], to_finding(match, column)))

    return group_by_path(issues)


def find_caret(following: list[str]) -> int:
    carets = [line.index("^") + 1 for line in following if line.strip() == "^"]
    return carets[0] if carets else 1


def to_finding(match: re.Match[str], column: int) -> Finding:
    message = match["message"]
    bug = re.match(r"\[(\w+)\] (.*)", message)
    code = f"errorprone:{bug[1]}" if bug else "javac"

    return Finding(
        line=int(match["line"]),
        column=column,
        code=code,
        message=bug[2] if bug else message,
        is_error=match["kind"] == "error",
    )
