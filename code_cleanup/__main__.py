import argparse
import logging
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path

from .discover import find_files
from .engine import clean_files
from .errors import ToolError
from .report import is_failure, render_report
from .settings import load_settings

log = logging.getLogger("code_cleanup")


@dataclass(frozen=True, slots=True)
class Options:
    root: Path
    config_path: Path | None
    check: bool
    report: str
    verbose: bool


def main(argv: Sequence[str] | None = None) -> int:
    options = parse_args(argv)
    configure_logging(options.verbose)

    try:
        settings = load_settings(options.root, options.config_path)
        paths = find_files(options.root, settings.exclude)
        results = clean_files(paths, options.root, settings, options.check)

    except ToolError as error:
        log.error("%s", error)
        return 1

    print(render_report(results, options.report, options.check))

    return 1 if is_failure(results, options.check) else 0


def parse_args(argv: Sequence[str] | None) -> Options:
    parser = argparse.ArgumentParser(
        prog="code-cleanup",
        description="Clean every file under ROOT to the house style, by language.",
    )
    parser.add_argument("root", type=Path, nargs="?", default=Path())
    parser.add_argument("--check", action="store_true", help="report only; never edit")
    parser.add_argument("--config", type=Path, help="default: ROOT/.code-cleanup.yaml")
    parser.add_argument("--report", choices=["text", "json", "junit"], default="text")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--version", action="version", version=version("code-cleanup"))

    namespace = parser.parse_args(argv)

    return Options(
        root=namespace.root,
        config_path=namespace.config,
        check=namespace.check,
        report=namespace.report,
        verbose=namespace.verbose,
    )


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


if __name__ == "__main__":
    raise SystemExit(main())
