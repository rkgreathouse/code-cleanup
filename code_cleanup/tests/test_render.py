import pytest

from ..errors import ConfigError
from ..render import to_ini, to_toml


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
