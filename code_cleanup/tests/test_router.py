from pathlib import Path

from ..router import route


def test_routes_python_sources_and_stubs() -> None:
    assert [route(Path(name)) is not None for name in ("a.py", "b.pyi")] == [True, True]


def test_skips_languages_without_a_plugin() -> None:
    assert route(Path("README.md")) is None
