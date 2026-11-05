from pathlib import Path

from ..project import find_minimum_python, parse_minimum


def test_reads_requires_python_from_pyproject(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.11"\n')

    assert find_minimum_python(tmp_path) == (3, 11)


def test_falls_back_to_setup_cfg_then_setup_py(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.black]\n")
    (tmp_path / "setup.py").write_text('setup(python_requires=">=3.8")\n')

    assert find_minimum_python(tmp_path) == (3, 8)

    (tmp_path / "setup.cfg").write_text("[options]\npython_requires = >=3.9\n")

    assert find_minimum_python(tmp_path) == (3, 9)


def test_declares_nothing_without_metadata(tmp_path: Path) -> None:
    assert find_minimum_python(tmp_path) is None


def test_takes_the_lower_bound_of_a_specifier() -> None:
    assert parse_minimum(">=3.10, <4") == (3, 10)
    assert parse_minimum("~=3.12") == (3, 12)
    assert parse_minimum("<4") is None
