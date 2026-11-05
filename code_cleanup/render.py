import json

from .errors import ConfigError


def to_toml(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"

    if isinstance(value, int | float):
        return str(value)

    if isinstance(value, str):
        return json.dumps(value)

    if isinstance(value, list):
        return "[" + ", ".join(to_toml(item) for item in value) + "]"

    if isinstance(value, dict):
        pairs = (
            f"{json.dumps(str(key))} = {to_toml(item)}" for key, item in value.items()
        )
        return "{ " + ", ".join(pairs) + " }"

    raise ConfigError(f"cannot pass {value!r} to a tool as a setting")


def to_ini(value: object) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"

    if isinstance(value, list):
        return ", ".join(to_ini(item) for item in value)

    if isinstance(value, str | int | float):
        return str(value)

    raise ConfigError(f"cannot pass {value!r} to a tool as a setting")
