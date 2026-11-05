import ast
from pathlib import Path

from ..findings import Finding
from ..settings import PythonSettings


def find_style_issues(
    tree: ast.Module, path: Path, settings: PythonSettings
) -> list[Finding]:
    findings = []

    if settings.relative_imports:
        findings += find_absolute_self_imports(tree, path)

    if not settings.allow_docstrings:
        findings += find_docstrings(tree)

    findings += find_extra_constants(tree, settings.max_module_constants)

    return findings


def find_absolute_self_imports(tree: ast.Module, path: Path) -> list[Finding]:
    package = find_top_package(path)

    if package is None:
        return []

    findings = []

    for node in ast.walk(tree):
        names = imported_modules(node)

        if any(is_inside(name, package) for name in names):
            findings.append(
                Finding(
                    line=node.lineno if isinstance(node, ast.stmt) else 1,
                    column=1,
                    code="CC101",
                    message=f"import from inside the {package} package relatively",
                    is_error=True,
                )
            )

    return findings


def imported_modules(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]

    if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
        return [node.module]

    return []


def is_inside(module: str, package: str) -> bool:
    return module == package or module.startswith(f"{package}.")


def find_top_package(path: Path) -> str | None:
    directory = path.resolve().parent
    package = None

    while (directory / "__init__.py").is_file():
        package = directory.name
        directory = directory.parent

    return package


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
    constants = [
        (node.lineno, name)
        for node in tree.body
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
