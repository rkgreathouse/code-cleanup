import ast
from pathlib import Path

from ..findings import Finding
from ..settings import PythonSettings


def find_logging_issues(
    tree: ast.Module, path: Path, settings: PythonSettings
) -> list[Finding]:
    if not settings.logging_checks:
        return []

    is_entry = path.name == "__main__.py"
    findings = []

    for node in ast.walk(tree):
        name = call_name(node)

        if not isinstance(node, ast.Call) or name is None:
            continue

        if name in ("logging.basicConfig", "basicConfig"):
            findings += check_basic_config(node, is_entry, settings)

        if name in ("logging.getLogger", "getLogger"):
            findings += check_logger_name(node, is_entry)

    return findings


def call_name(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Call):
        return None

    if isinstance(node.func, ast.Name):
        return node.func.id

    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
        return f"{node.func.value.id}.{node.func.attr}"

    return None


def check_basic_config(
    node: ast.Call, is_entry: bool, settings: PythonSettings
) -> list[Finding]:
    if not is_entry:
        return [finding(node, "CC201", "configure logging once, in __main__.py")]

    keywords = {keyword.arg: keyword.value for keyword in node.keywords}
    wanted = {"format": settings.log_format, "datefmt": settings.log_datefmt}

    return [
        finding(node, "CC203", f"basicConfig needs {key}={value!r}")
        for key, value in wanted.items()
        if not is_constant(keywords.get(key), value)
    ]


def check_logger_name(node: ast.Call, is_entry: bool) -> list[Finding]:
    argument = node.args[0] if node.args else None
    is_module_name = isinstance(argument, ast.Name) and argument.id == "__name__"
    is_literal = isinstance(argument, ast.Constant) and isinstance(argument.value, str)

    if is_entry and not is_literal:
        return [finding(node, "CC202", 'the entry module logs as getLogger("<tool>")')]

    if not is_entry and not is_module_name:
        return [finding(node, "CC202", "modules log as getLogger(__name__)")]

    return []


def is_constant(node: ast.expr | None, value: str) -> bool:
    return isinstance(node, ast.Constant) and node.value == value


def finding(node: ast.Call, code: str, message: str) -> Finding:
    return Finding(
        line=node.lineno,
        column=node.col_offset + 1,
        code=code,
        message=message,
        is_error=True,
    )
