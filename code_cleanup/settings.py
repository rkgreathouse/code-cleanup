from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

import yaml

from .errors import ConfigError
from .render import to_ini, to_toml


@dataclass(frozen=True, slots=True)
class PythonSettings:
    ruff_toml: str
    mypy_enabled: bool
    mypy_ini: str
    blank_lines_around_blocks: bool
    blank_line_before_block_comment: bool
    blank_line_before_except: bool
    tight_else: bool
    relative_imports: bool
    allow_docstrings: bool
    allow_environment: bool
    max_module_constants: int
    logging_checks: bool
    log_format: str
    log_datefmt: str


@dataclass(frozen=True, slots=True)
class IgnoreSettings:
    sort_blocks: bool
    require_headers: bool


@dataclass(frozen=True, slots=True)
class Settings:
    profile: str
    exclude: tuple[str, ...]
    warn_lines: int
    max_lines: int
    python: PythonSettings
    ignore: IgnoreSettings


def load_settings(root: Path, config_path: Path | None) -> Settings:
    raw = parse_yaml(
        files("code_cleanup").joinpath("style.yaml").read_text(), "style.yaml"
    )
    project_path = config_path or root / ".code-cleanup.yaml"

    if config_path is not None or project_path.is_file():
        raw = merge(raw, read_yaml(project_path))

    return parse_settings(raw, project_path)


def read_yaml(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise ConfigError(f"config not found: {path}")

    return parse_yaml(path.read_text(), str(path))


def parse_yaml(text: str, source: str) -> dict[str, object]:
    try:
        data = yaml.safe_load(text)

    except yaml.YAMLError as error:
        raise ConfigError(f"{source}: not valid YAML: {error}") from error

    # an empty project file means "no overrides", not a broken config
    if data is None:
        return {}

    if not isinstance(data, dict):
        raise ConfigError(f"{source}: config must be a mapping")

    return data


def merge(base: dict[str, object], override: dict[str, object]) -> dict[str, object]:
    merged = dict(base)

    for key, value in override.items():
        current = merged.get(key)

        if isinstance(current, dict) and isinstance(value, dict):
            merged[key] = merge(current, value)
        else:
            merged[key] = value

    return merged


def parse_settings(raw: dict[str, object], path: Path) -> Settings:
    exclude = raw.get("exclude")
    profile = raw.get("profile")
    file_length = section(raw, "file_length", path)

    if profile not in ("none", "cli"):
        raise ConfigError(f"{path}: profile must be none or cli, not {profile!r}")

    if not isinstance(exclude, list):
        raise ConfigError(f"{path}: exclude must be a list")

    return Settings(
        profile=str(profile),
        exclude=tuple(str(name) for name in exclude),
        warn_lines=integer(file_length, "warn", path),
        max_lines=integer(file_length, "max", path),
        python=parse_python(section(raw, "python", path), path),
        ignore=parse_ignore(section(raw, "ignore", path), path),
    )


def parse_ignore(raw: dict[str, object], path: Path) -> IgnoreSettings:
    return IgnoreSettings(
        sort_blocks=boolean(raw, "sort_blocks", path),
        require_headers=boolean(raw, "require_headers", path),
    )


def parse_python(raw: dict[str, object], path: Path) -> PythonSettings:
    spacing = section(raw, "spacing", path)
    checks = section(raw, "checks", path)
    ruff = section(raw, "ruff", path)
    mypy = section(raw, "mypy", path)
    mypy_config = section(mypy, "config", path)
    logs = section(raw, "logging", path)

    return PythonSettings(
        ruff_toml="".join(f"{key} = {to_toml(value)}\n" for key, value in ruff.items()),
        mypy_enabled=boolean(mypy, "enabled", path),
        mypy_ini="[mypy]\n"
        + "".join(f"{key} = {to_ini(value)}\n" for key, value in mypy_config.items()),
        blank_lines_around_blocks=boolean(spacing, "around_blocks", path),
        blank_line_before_block_comment=boolean(spacing, "before_block_comment", path),
        blank_line_before_except=boolean(spacing, "before_except", path),
        tight_else=boolean(spacing, "tight_else", path),
        relative_imports=boolean(checks, "relative_imports", path),
        allow_docstrings=boolean(checks, "allow_docstrings", path),
        allow_environment=boolean(checks, "allow_environment", path),
        max_module_constants=integer(checks, "max_module_constants", path),
        logging_checks=boolean(logs, "check", path),
        log_format=string(logs, "format", path),
        log_datefmt=string(logs, "datefmt", path),
    )


def section(raw: dict[str, object], key: str, path: Path) -> dict[str, object]:
    value = raw.get(key)

    if not isinstance(value, dict):
        raise ConfigError(f"{path}: {key} must be a mapping")

    return value


def boolean(raw: dict[str, object], key: str, path: Path) -> bool:
    value = raw.get(key)

    if not isinstance(value, bool):
        raise ConfigError(f"{path}: {key} must be true or false")

    return value


def integer(raw: dict[str, object], key: str, path: Path) -> int:
    value = raw.get(key)

    # bool is a subclass of int, and "max: true" is a typo, not a limit of 1
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{path}: {key} must be an integer")

    return value


def string(raw: dict[str, object], key: str, path: Path) -> str:
    value = raw.get(key)

    if not isinstance(value, str):
        raise ConfigError(f"{path}: {key} must be a string")

    return value
