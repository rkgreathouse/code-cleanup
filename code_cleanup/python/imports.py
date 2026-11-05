import ast
import re
from pathlib import Path

from ..findings import Finding


def relativize_imports(text: str, path: Path) -> str:
    package = find_package_parts(path)
    lines = text.splitlines(keepends=True)

    if not package:
        return text

    for node in ast.walk(ast.parse(text)):
        if not isinstance(node, ast.ImportFrom) or node.level != 0 or not node.module:
            continue

        if is_inside(node.module, package[0]):
            relative = relative_module(node.module, package)
            pattern = rf"\bfrom\s+{re.escape(node.module)}(?=\s)"
            line = lines[node.lineno - 1]
            lines[node.lineno - 1] = re.sub(pattern, f"from {relative}", line, count=1)

    return "".join(lines)


def relative_module(module: str, package: list[str]) -> str:
    target = module.split(".")
    shared = 0

    while shared < min(len(target), len(package)) and target[shared] == package[shared]:
        shared += 1

    return "." * (len(package) - shared + 1) + ".".join(target[shared:])


def find_absolute_self_imports(tree: ast.Module, path: Path) -> list[Finding]:
    package = find_package_parts(path)

    if not package:
        return []

    return [
        Finding(
            line=node.lineno,
            column=node.col_offset + 1,
            code="CC101",
            message=f"import from inside the {package[0]} package relatively",
            is_error=True,
        )
        for node in ast.walk(tree)
        if isinstance(node, ast.stmt) and imports_package(node, package[0])
    ]


def imports_package(node: ast.stmt, package: str) -> bool:
    return any(is_inside(name, package) for name in imported_modules(node))


def imported_modules(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]

    if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
        return [node.module]

    return []


def is_inside(module: str, package: str) -> bool:
    return module == package or module.startswith(f"{package}.")


def find_package_parts(path: Path) -> list[str]:
    directory = path.resolve().parent
    parts = []

    while (directory / "__init__.py").is_file():
        parts.append(directory.name)
        directory = directory.parent

    return parts[::-1]
