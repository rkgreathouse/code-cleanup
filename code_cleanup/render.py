import json
from xml.sax.saxutils import quoteattr

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


def to_option(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"

    if isinstance(value, str | int):
        return str(value)

    raise ConfigError(f"cannot pass {value!r} to a tool as an option")


def to_checkstyle_xml(
    checker: dict[str, object], tree_walker: dict[str, object]
) -> str:
    walker = to_module("TreeWalker", to_modules(tree_walker, "    "), "  ")
    body = to_modules(checker, "  ") + walker

    return (
        '<?xml version="1.0"?>\n'
        '<!DOCTYPE module PUBLIC "-//Checkstyle//DTD Checkstyle Configuration 1.3//EN"'
        ' "https://checkstyle.org/dtds/configuration_1_3.dtd">\n'
        + to_module("Checker", body, "")
    )


def to_modules(modules: dict[str, object], indent: str) -> str:
    return "".join(
        to_module(name, to_properties(name, value, indent + "  "), indent)
        for name, value in modules.items()
    )


def to_module(name: str, body: str, indent: str) -> str:
    if not body:
        return f"{indent}<module name={quoteattr(name)}/>\n"

    return f"{indent}<module name={quoteattr(name)}>\n{body}{indent}</module>\n"


def to_properties(name: str, value: object, indent: str) -> str:

    # a module listed with no settings runs with Checkstyle's defaults
    if value is None:
        return ""

    if not isinstance(value, dict):
        raise ConfigError(f"checkstyle module {name} must map property names to values")

    return "".join(
        f"{indent}<property name={quoteattr(str(key))} "
        f"value={quoteattr(to_property(item))}/>\n"
        for key, item in value.items()
    )


def to_property(value: object) -> str:
    if isinstance(value, list):
        return ",".join(to_option(item) for item in value)

    return to_option(value)
