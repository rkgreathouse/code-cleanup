from pathlib import Path

import pytest

from ..errors import ConfigError
from ..settings import load_settings, merge


def test_loads_the_house_style_without_a_project_file(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None)

    assert settings.max_lines == 400
    assert settings.python.tight_else is True
    assert 'lint.ignore = ["TID252"]\n' in settings.python.ruff_toml


def test_project_file_overrides_single_keys(tmp_path: Path) -> None:
    (tmp_path / ".code-cleanup.yaml").write_text(
        "file_length:\n  max: 500\npython:\n  ruff:\n    line-length: 100\n"
    )

    settings = load_settings(tmp_path, None)

    assert settings.max_lines == 500
    assert settings.warn_lines == 350
    assert "line-length = 100\n" in settings.python.ruff_toml
    assert "target-version" in settings.python.ruff_toml


def test_explicit_config_must_exist(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="config not found"):
        load_settings(tmp_path, tmp_path / "missing.yaml")


def test_wrong_type_names_the_key(tmp_path: Path) -> None:
    (tmp_path / ".code-cleanup.yaml").write_text(
        "python:\n  spacing:\n    tight_else: 1\n"
    )

    with pytest.raises(ConfigError, match="tight_else"):
        load_settings(tmp_path, None)


def test_merge_replaces_lists_and_merges_mappings() -> None:
    base: dict[str, object] = {"a": {"b": 1, "c": 2}, "d": [1, 2]}

    assert merge(base, {"a": {"c": 3}, "d": [9]}) == {"a": {"b": 1, "c": 3}, "d": [9]}


def test_profile_must_be_known(tmp_path: Path) -> None:
    (tmp_path / ".code-cleanup.yaml").write_text("profile: webapp\n")

    with pytest.raises(ConfigError, match="profile must be none or cli"):
        load_settings(tmp_path, None)
