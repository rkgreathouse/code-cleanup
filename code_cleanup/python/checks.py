import ast
from pathlib import Path

from ..findings import Finding
from ..settings import PythonSettings

ENVIRONMENT = {"environ", "environb", "getenv", "getenvb"}


def find_style_issues(
    tree: ast.Module, path: Path, settings: PythonSettings
) -> list[Finding]:
    findings = []

    if not settings.allow_environment:
        findings += find_environment_reads(tree)

    if not settings.allow_docstrings:
        findings += find_docstrings(tree)

    findings += find_extra_constants(tree, settings.max_module_constants)

    return findings


def find_environment_reads(tree: ast.Module) -> list[Finding]:
    return [
        Finding(
            line=node.lineno,
            column=node.col_offset + 1,
            code="CC104",
            message="reads the environment; take it as a flag or from config.yaml",
            is_error=True,
        )
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute | ast.ImportFrom) and reads_environment(node)
    ]


def reads_environment(node: ast.Attribute | ast.ImportFrom) -> bool:
    if isinstance(node, ast.ImportFrom):
        return node.module == "os" and any(
            alias.name in ENVIRONMENT for alias in node.names
        )

    return (
        isinstance(node.value, ast.Name)
        and node.value.id == "os"
        and node.attr in ENVIRONMENT
    )


def find_docstrings(tree: ast.Module) -> list[Finding]:
    owners = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)

    return [
        Finding(
            line=node.body[0].lineno,
            column=node.body[0].col_offset + 1,
            code="CC103",
            message="docstring; let names and small functions carry the meaning",
            is_error=True,
        )
        for node in ast.walk(tree)
        if isinstance(node, owners) and ast.get_docstring(node, clean=False) is not None
    ]


def find_extra_constants(tree: ast.Module, limit: int) -> list[Finding]:
    constants = []

    for node in tree.body:
        constants += [
            (node.lineno, name)
            for name in assigned_names(node)
            if name.isupper() and not name.startswith("__")
        ]

    return [
        Finding(
            line=line,
            column=1,
            code="CC102",
            message=f"constant {number} of at most {limit}; move {name} to config",
            is_error=True,
        )
        for number, (line, name) in enumerate(constants, start=1)
        if number > limit
    ]


def assigned_names(node: ast.stmt) -> list[str]:
    if isinstance(node, ast.Assign):
        return [target.id for target in node.targets if isinstance(target, ast.Name)]

    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return [node.target.id]

    return []
