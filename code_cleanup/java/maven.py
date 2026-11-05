import hashlib
import logging
import shutil
import subprocess
from pathlib import Path

from ..errors import MavenError, ToolNotFoundError

log = logging.getLogger(__name__)

JDK_EXPORTS = (
    "api",
    "code",
    "comp",
    "file",
    "main",
    "model",
    "parser",
    "processing",
    "tree",
    "util",
)


def find_jdk_tool(name: str) -> str:
    found = shutil.which(name)

    if found is None:
        raise ToolNotFoundError(
            f"{name} is not on PATH; Java needs a JDK 21+ and Maven"
        )

    return found


def compiler_exports(prefix: str) -> list[str]:
    flags = [
        f"{prefix}--add-exports=jdk.compiler/com.sun.tools.javac.{name}=ALL-UNNAMED"
        for name in JDK_EXPORTS
    ]

    return [
        *flags,
        f"{prefix}--add-opens=jdk.compiler/com.sun.tools.javac.code=ALL-UNNAMED",
        f"{prefix}--add-opens=jdk.compiler/com.sun.tools.javac.comp=ALL-UNNAMED",
    ]


def group_by_module(root: Path, paths: list[Path]) -> dict[Path, list[Path]]:
    modules: dict[Path, list[Path]] = {}

    for path in paths:
        module = find_module(root, path)
        modules[module] = [*modules.get(module, []), path]

    return modules


def find_module(root: Path, path: Path) -> Path:
    for folder in path.parents:
        if (folder / "pom.xml").is_file():
            return folder

        # a pom.xml above the scanned folder belongs to another project
        if folder == root:
            break

    return root


def resolve_tool(coordinate: str) -> str:
    folder = Path.home() / ".cache" / "code-cleanup" / "java" / cache_name(coordinate)
    classpath_file = folder / "classpath.txt"

    # named by coordinate, so a cached classpath already holds exactly this version
    if classpath_file.is_file():
        return classpath_file.read_text().strip()

    log.info("resolving %s through Maven (once)", coordinate)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "pom.xml").write_text(tool_pom(coordinate))
    result = build_classpath(folder, classpath_file, scope="runtime")

    if result.returncode != 0:
        raise MavenError(f"could not resolve {coordinate}: {last_error(result)}")

    return classpath_file.read_text().strip()


def resolve_project(module: Path, output: Path) -> str | None:
    result = build_classpath(module, output, scope="test")

    if result.returncode != 0:
        log.warning("no classpath for %s: %s", module, last_error(result))
        return None

    return output.read_text().strip()


def build_classpath(
    folder: Path, output: Path, scope: str
) -> subprocess.CompletedProcess[str]:
    command = [find_jdk_tool("mvn"), "-q", "-B", "-f", str(folder / "pom.xml")]
    command += ["dependency:build-classpath", f"-Dmdep.outputFile={output}"]

    return subprocess.run(
        [*command, f"-Dmdep.includeScope={scope}"],
        capture_output=True,
        text=True,
        check=False,
    )


def cache_name(coordinate: str) -> str:
    digest = hashlib.sha256(coordinate.encode()).hexdigest()[:12]
    return f"{coordinate.split(':')[1]}-{digest}"


def tool_pom(coordinate: str) -> str:
    group, artifact, version = parse_coordinate(coordinate)

    return (
        '<project xmlns="http://maven.apache.org/POM/4.0.0">\n'
        "  <modelVersion>4.0.0</modelVersion>\n"
        "  <groupId>code-cleanup</groupId>\n"
        f"  <artifactId>{artifact}-tool</artifactId>\n"
        "  <version>1</version>\n"
        "  <packaging>pom</packaging>\n"
        "  <dependencies>\n"
        "    <dependency>\n"
        f"      <groupId>{group}</groupId>\n"
        f"      <artifactId>{artifact}</artifactId>\n"
        f"      <version>{version}</version>\n"
        "    </dependency>\n"
        "  </dependencies>\n"
        "</project>\n"
    )


def parse_coordinate(coordinate: str) -> tuple[str, str, str]:
    parts = coordinate.split(":")

    if len(parts) != 3 or not all(parts):
        raise MavenError(f"tool must be group:artifact:version, not {coordinate!r}")

    return parts[0], parts[1], parts[2]


def last_error(result: subprocess.CompletedProcess[str]) -> str:
    lines = [
        line
        for line in (result.stdout + result.stderr).splitlines()
        if line.strip() and not line.startswith("Picked up")
    ]

    return lines[0] if lines else f"exit {result.returncode}"
