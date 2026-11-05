import ast
from pathlib import Path

from ..findings import Finding, group_by_path

SHARED_PACKAGE = "utils"
MAIN_GUARD = 'if __name__ == "__main__":\n    raise SystemExit(main())'

type Issue = tuple[Path, Finding]


def find_layout_issues(root: Path, texts: dict[Path, str]) -> dict[Path, list[Finding]]:
    trees = {path: ast.parse(text) for path, text in texts.items()}
    packages = find_packages(root, trees)
    tools = sorted(packages - {SHARED_PACKAGE})
    issues = [
        *find_loose_modules(root, trees),
        *find_untested_modules(root, trees, packages),
        *find_cross_tool_imports(root, trees, packages),
    ]

    for tool in tools:
        issues += check_entry_module(root / tool, trees)
        issues += check_errors_module(root / tool, trees)

    return group_by_path(issues)


def find_packages(root: Path, trees: dict[Path, ast.Module]) -> set[str]:
    return {
        path.relative_to(root).parts[0]
        for path in trees
        if len(path.relative_to(root).parts) == 2 and path.name == "__init__.py"
    }


def find_loose_modules(root: Path, trees: dict[Path, ast.Module]) -> list[Issue]:
    message = "module at the repo root; put it in a package run with python -m"

    return [
        issue(path, 1, "CC301", message)
        for path in trees
        if len(path.relative_to(root).parts) == 1
    ]


def find_untested_modules(
    root: Path, trees: dict[Path, ast.Module], packages: set[str]
) -> list[Issue]:
    issues = []

    for path, tree in sorted(trees.items()):
        parts = path.relative_to(root).parts
        is_module = parts[0] in packages and "tests" not in parts

        # modules holding only classes and constants, like errors.py, need no tests
        if not is_module or path.name == "__init__.py" or not defines_function(tree):
            continue

        expected = root / parts[0] / "tests" / expected_test_name(parts[1:])

        if expected not in trees:
            message = f"no tests; expected {expected.relative_to(root)}"
            issues.append(issue(path, 1, "CC302", message))

    return issues


def expected_test_name(parts: tuple[str, ...]) -> str:
    stem = Path(parts[-1]).stem.strip("_")
    return "test_" + "_".join([*parts[:-1], stem]) + ".py"


def defines_function(tree: ast.Module) -> bool:
    return any(
        isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) for node in tree.body
    )


def find_cross_tool_imports(
    root: Path, trees: dict[Path, ast.Module], packages: set[str]
) -> list[Issue]:
    issues = []

    for path, tree in sorted(trees.items()):
        own = path.relative_to(root).parts[0]

        for node in ast.walk(tree):
            others = {name.split(".")[0] for name in imported_names(node)}
            tools = sorted(others & packages - {own, SHARED_PACKAGE})

            if tools and isinstance(node, ast.stmt):
                imported = ", ".join(tools)
                message = f"imports tool {imported}; share code through utils instead"
                issues.append(issue(path, node.lineno, "CC305", message))

    return issues


def imported_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]

    if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
        return [node.module]

    return []


def check_entry_module(package: Path, trees: dict[Path, ast.Module]) -> list[Issue]:
    entry = package / "__main__.py"
    tree = trees.get(entry)

    if tree is None:
        message = f"no __main__.py; a tool runs as python -m {package.name}"
        return [issue(package / "__init__.py", 1, "CC303", message)]

    problems = [
        *check_main_function(tree),
        *check_options(tree),
        *check_main_guard(tree),
    ]

    return [issue(entry, line, "CC303", message) for line, message in problems]


def check_main_function(tree: ast.Module) -> list[tuple[int, str]]:
    main = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "main"
        ),
        None,
    )

    if main is None:
        return [(1, "no main(argv) function")]

    if not (isinstance(main.returns, ast.Name) and main.returns.id == "int"):
        return [(main.lineno, "main must return an int exit code")]

    return []


def check_options(tree: ast.Module) -> list[tuple[int, str]]:
    uses_argparse = any("argparse" in imported_names(node) for node in tree.body)
    options = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "Options"
        ),
        None,
    )

    if not uses_argparse:
        return []

    if options is None:
        return [(1, "parsed flags belong in a frozen Options dataclass")]

    if not is_frozen_dataclass(options):
        return [(options.lineno, "Options must be @dataclass(frozen=True, slots=True)")]

    return []


def is_frozen_dataclass(node: ast.ClassDef) -> bool:
    for decorator in node.decorator_list:
        is_dataclass_call = (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Name)
            and decorator.func.id == "dataclass"
        )
        keywords = {
            keyword.arg
            for keyword in getattr(decorator, "keywords", [])
            if isinstance(keyword.value, ast.Constant) and keyword.value.value is True
        }

        if is_dataclass_call and {"frozen", "slots"} <= keywords:
            return True

    return False


def check_main_guard(tree: ast.Module) -> list[tuple[int, str]]:
    expected = ast.unparse(ast.parse(MAIN_GUARD))
    last = tree.body[-1] if tree.body else None

    if last is not None and ast.unparse(last) == expected:
        return []

    line = last.lineno if last is not None else 1
    return [(line, "end with: " + " ".join(MAIN_GUARD.split()))]


def check_errors_module(package: Path, trees: dict[Path, ast.Module]) -> list[Issue]:
    errors = package / "errors.py"
    tree = trees.get(errors)

    if tree is None:
        message = "no errors.py; define ToolError(Exception) and one subclass per area"
        return [issue(package / "__init__.py", 1, "CC304", message)]

    if not any(is_tool_error(node) for node in tree.body):
        return [
            issue(errors, 1, "CC304", "errors.py needs a ToolError(Exception) base")
        ]

    return []


def is_tool_error(node: ast.stmt) -> bool:
    return (
        isinstance(node, ast.ClassDef)
        and node.name == "ToolError"
        and any(
            isinstance(base, ast.Name) and base.id == "Exception" for base in node.bases
        )
    )


def issue(path: Path, line: int, code: str, message: str) -> Issue:
    return (
        path,
        Finding(line=line, column=1, code=code, message=message, is_error=True),
    )
