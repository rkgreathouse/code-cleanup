from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

import yaml

from .errors import ConfigError
from .project import find_java_release, find_minimum_python
from .render import to_checkstyle_xml, to_ini, to_option, to_toml

MYPY_OLDEST = (3, 10)
PROFILES = ("none", "cli", "service")


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
    simple_comprehensions: bool
    suggest_walrus: bool
    max_module_constants: int
    logging_checks: bool
    log_format: str
    log_datefmt: str


@dataclass(frozen=True, slots=True)
class JavaSettings:
    release: int
    formatter: str
    checkstyle: str
    error_prone: str
    checkstyle_xml: str
    error_prone_enabled: bool
    error_prone_flags: tuple[str, ...]
    blank_lines_around_blocks: bool
    blank_line_before_block_comment: bool
    blank_line_before_catch: bool
    allow_javadoc: bool
    allow_environment: bool
    simple_streams: bool
    max_class_constants: int
    max_nesting: int
    logging_checks: bool


@dataclass(frozen=True, slots=True)
class IgnoreSettings:
    sort_blocks: bool
    require_headers: bool


@dataclass(frozen=True, slots=True)
class TomlSettings:
    taplo_options: tuple[str, ...]
    blank_line_before_tables: bool


@dataclass(frozen=True, slots=True)
class Settings:
    profile: str
    exclude: tuple[str, ...]
    warn_lines: int
    max_lines: int
    python: PythonSettings
    java: JavaSettings
    ignore: IgnoreSettings
    toml: TomlSettings


def load_settings(root: Path, config_path: Path | None) -> Settings:
    raw = parse_yaml(
        files("code_cleanup").joinpath("style.yaml").read_text(), "style.yaml"
    )
    project_path = config_path or root / ".code-cleanup.yaml"
    raw = merge(raw, target_python(root))
    raw = merge(raw, target_java(root))

    if config_path is not None or project_path.is_file():
        raw = merge(raw, read_yaml(project_path))

    return parse_settings(raw, project_path)


def target_python(root: Path) -> dict[str, object]:
    version = find_minimum_python(root)

    if version is None:
        return {}

    major, minor = version
    checked = max(version, MYPY_OLDEST)

    return {
        "python": {
            "ruff": {"target-version": f"py{major}{minor}"},
            "mypy": {"config": {"python_version": f"{checked[0]}.{checked[1]}"}},
        }
    }


def target_java(root: Path) -> dict[str, object]:
    release = find_java_release(root)
    return {} if release is None else {"java": {"release": release}}


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

    if profile not in PROFILES:
        known = ", ".join(PROFILES)
        raise ConfigError(f"{path}: profile must be one of {known}, not {profile!r}")

    if not isinstance(exclude, list):
        raise ConfigError(f"{path}: exclude must be a list")

    return Settings(
        profile=str(profile),
        exclude=tuple(str(name) for name in exclude),
        warn_lines=integer(file_length, "warn", path),
        max_lines=integer(file_length, "max", path),
        python=parse_python(section(raw, "python", path), path),
        java=parse_java(section(raw, "java", path), path),
        ignore=parse_ignore(section(raw, "ignore", path), path),
        toml=parse_toml(section(raw, "toml", path), path),
    )


def parse_toml(raw: dict[str, object], path: Path) -> TomlSettings:
    taplo = section(raw, "taplo", path)

    return TomlSettings(
        taplo_options=tuple(
            f"{key}={to_option(value)}" for key, value in taplo.items()
        ),
        blank_line_before_tables=boolean(raw, "blank_line_before_tables", path),
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
        simple_comprehensions=boolean(checks, "simple_comprehensions", path),
        suggest_walrus=boolean(checks, "suggest_walrus", path),
        max_module_constants=integer(checks, "max_module_constants", path),
        logging_checks=boolean(logs, "check", path),
        log_format=string(logs, "format", path),
        log_datefmt=string(logs, "datefmt", path),
    )


def parse_java(raw: dict[str, object], path: Path) -> JavaSettings:
    spacing = section(raw, "spacing", path)
    checks = section(raw, "checks", path)
    tools = section(raw, "tools", path)
    checkstyle = section(raw, "checkstyle", path)
    error_prone = section(raw, "error_prone", path)
    severities = section(error_prone, "checks", path)

    return JavaSettings(
        release=integer(raw, "release", path),
        formatter=string(tools, "google-java-format", path),
        checkstyle=string(tools, "checkstyle", path),
        error_prone=string(tools, "error-prone", path),
        checkstyle_xml=to_checkstyle_xml(
            section(checkstyle, "checker", path),
            section(checkstyle, "tree_walker", path),
        ),
        error_prone_enabled=boolean(error_prone, "enabled", path),
        error_prone_flags=tuple(
            f"-Xep:{name}:{to_option(level)}" for name, level in severities.items()
        ),
        blank_lines_around_blocks=boolean(spacing, "around_blocks", path),
        blank_line_before_block_comment=boolean(spacing, "before_block_comment", path),
        blank_line_before_catch=boolean(spacing, "before_catch", path),
        allow_javadoc=boolean(checks, "allow_javadoc", path),
        allow_environment=boolean(checks, "allow_environment", path),
        simple_streams=boolean(checks, "simple_streams", path),
        max_class_constants=integer(checks, "max_class_constants", path),
        max_nesting=integer(checks, "max_nesting", path),
        logging_checks=boolean(section(raw, "logging", path), "check", path),
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
