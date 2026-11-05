import ast
from dataclasses import replace
from pathlib import Path

from ..python.logs import find_logging_issues
from .test_python_spacing import make_settings

HOUSE_CONFIG = """logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
"""


def codes(source: str, name: str) -> list[str]:
    tree = ast.parse(source)
    findings = find_logging_issues(tree, Path("tool") / name, make_settings())

    return [finding.code for finding in findings]


def test_entry_module_configures_with_the_house_format() -> None:
    source = f'log = logging.getLogger("tool")\n{HOUSE_CONFIG}'

    assert codes(source, "__main__.py") == []


def test_only_the_entry_module_configures_logging() -> None:
    assert codes(HOUSE_CONFIG, "scan.py") == ["CC201"]


def test_flags_a_format_that_is_not_the_house_format() -> None:
    assert codes("logging.basicConfig(level=10)\n", "__main__.py") == ["CC203", "CC203"]


def test_modules_name_their_logger_after_themselves() -> None:
    assert codes("log = logging.getLogger(__name__)\n", "scan.py") == []
    assert codes('log = logging.getLogger("scan")\n', "scan.py") == ["CC202"]
    assert codes("log = logging.getLogger(__name__)\n", "__main__.py") == ["CC202"]


def test_can_be_switched_off() -> None:
    settings = replace(make_settings(), logging_checks=False)
    tree = ast.parse(HOUSE_CONFIG)

    assert find_logging_issues(tree, Path("scan.py"), settings) == []
