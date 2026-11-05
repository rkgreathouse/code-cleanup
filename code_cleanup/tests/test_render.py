import pytest

from ..errors import ConfigError
from ..render import to_checkstyle_xml, to_ini, to_toml


def test_renders_nested_values_as_inline_toml() -> None:
    value = {"**/__main__.py": ["T201"], "strict": True, "limit": 4}

    assert (
        to_toml(value)
        == '{ "**/__main__.py" = ["T201"], "strict" = true, "limit" = 4 }'
    )


def test_rejects_values_toml_cannot_hold() -> None:
    with pytest.raises(ConfigError):
        to_toml(None)


def test_renders_ini_values_the_way_mypy_reads_them() -> None:
    assert [to_ini(True), to_ini("3.14"), to_ini(["a", "b"])] == [
        "True",
        "3.14",
        "a, b",
    ]


def test_renders_checkstyle_modules_under_checker_and_tree_walker() -> None:
    xml = to_checkstyle_xml(
        {"LineLength": {"max": 100}}, {"AvoidStarImport": None, "Regexp": {"x": [1, 2]}}
    )

    assert '<module name="Checker">\n  <module name="LineLength">\n' in xml
    assert '    <property name="max" value="100"/>\n' in xml
    assert '    <module name="AvoidStarImport"/>\n' in xml
    assert '      <property name="x" value="1,2"/>\n' in xml


def test_rejects_a_checkstyle_module_with_a_plain_value() -> None:
    with pytest.raises(ConfigError, match="LineLength"):
        to_checkstyle_xml({"LineLength": 100}, {})
