from pathlib import Path

from ..router import route


def test_routes_python_sources_and_stubs() -> None:
    assert [route(Path(name)) is not None for name in ("a.py", "b.pyi")] == [True, True]


def test_skips_languages_without_a_plugin() -> None:
    assert route(Path("README.md")) is None


def test_routes_ignore_files_by_name() -> None:
    language = route(Path("sub/.gitignore"))

    assert language is not None and language.name == "ignore"


def test_routes_java_sources() -> None:
    language = route(Path("src/main/java/A.java"))

    assert language is not None and language.name == "java"
