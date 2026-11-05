from dataclasses import replace
from pathlib import Path

from ..java.logs import find_logging_issues
from ..java.syntax import parse_java
from ..settings import load_settings

GOOD = """import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

class Service {
  private static final Logger log = LoggerFactory.getLogger(Service.class);

  void f(String name) {
    log.info("added {}", name);
  }
}
"""


def codes(source: str, tmp_path: Path) -> list[str]:
    settings = load_settings(tmp_path, None).java
    return [
        finding.code for finding in find_logging_issues(parse_java(source), settings)
    ]


def test_accepts_the_house_logger(tmp_path: Path) -> None:
    assert codes(GOOD, tmp_path) == []


def test_reports_a_logger_of_another_shape(tmp_path: Path) -> None:
    wrong_name = GOOD.replace("Logger log =", "Logger LOG =")
    wrong_class = GOOD.replace("getLogger(Service.class)", "getLogger(Other.class)")
    log4j = GOOD.replace("LoggerFactory.getLogger", "LogManager.getLogger")

    assert codes(wrong_name, tmp_path) == ["CC202"]
    assert codes(wrong_class, tmp_path) == ["CC202"]
    assert codes(log4j, tmp_path) == ["CC202"]


def test_reports_configuring_logging_in_code(tmp_path: Path) -> None:
    source = "import org.apache.logging.log4j.core.config.Configurator;\n" + GOOD

    assert codes(source, tmp_path) == ["CC201"]


def test_reports_a_message_built_before_the_call(tmp_path: Path) -> None:
    joined = GOOD.replace('"added {}", name', '"added " + name')
    formatted = GOOD.replace('"added {}", name', 'String.format("added %s", name)')

    assert codes(joined, tmp_path) == ["CC204"]
    assert codes(formatted, tmp_path) == ["CC204"]


def test_can_be_switched_off(tmp_path: Path) -> None:
    settings = replace(load_settings(tmp_path, None).java, logging_checks=False)
    source = GOOD.replace("Logger log =", "Logger LOG =")

    assert find_logging_issues(parse_java(source), settings) == []
