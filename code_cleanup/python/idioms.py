import ast
from collections import Counter

from ..findings import Finding
from ..settings import PythonSettings

COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


def find_idiom_issues(tree: ast.Module, settings: PythonSettings) -> list[Finding]:
    findings = []

    if settings.simple_comprehensions:
        findings += find_complex_comprehensions(tree)

    if settings.suggest_walrus:
        findings += find_walrus_candidates(tree)

    return findings


def find_complex_comprehensions(tree: ast.Module) -> list[Finding]:
    findings = []

    for node in ast.walk(tree):
        if not isinstance(node, COMPREHENSIONS):
            continue

        loops = len(node.generators)
        conditions = sum(len(generator.ifs) for generator in node.generators)
        nested = any(
            isinstance(inner, COMPREHENSIONS)
            for inner in ast.walk(node)
            if inner is not node
        )

        if loops > 1 or conditions > 1 or nested:
            findings.append(
                Finding(
                    line=node.lineno,
                    column=node.col_offset + 1,
                    code="CC105",
                    message="keep comprehensions to one for and one if; use a loop",
                    is_error=True,
                )
            )

    return findings


def find_walrus_candidates(tree: ast.Module) -> list[Finding]:
    candidates = {}

    for function in ast.walk(tree):
        if not isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef):
            continue

        uses = count_names(function)

        for assign, branch in find_assign_then_if(function):
            name = assign.targets[0]

            if not isinstance(name, ast.Name):
                continue

            is_tested = tests_only(branch.test, name.id)
            local_uses = count_names(assign, branch)[name.id]

            # used anywhere else, the name has a life of its own; keep the assignment
            if is_tested and uses[name.id] == local_uses:
                candidates[assign.lineno] = name.id

    return [
        Finding(
            line=line,
            column=1,
            code="CC106",
            message=f"{name} is only tested here; use if {name} := ...",
            is_error=False,
        )
        for line, name in sorted(candidates.items())
    ]


def find_assign_then_if(function: ast.AST) -> list[tuple[ast.Assign, ast.If]]:
    pairs = []

    for node in ast.walk(function):
        for field in ("body", "orelse", "finalbody"):
            body = getattr(node, field, None)

            if not isinstance(body, list):
                continue

            for first, second in zip(body, body[1:], strict=False):
                if is_simple_assign(first) and isinstance(second, ast.If):
                    pairs.append((first, second))

    return pairs


def tests_only(test: ast.expr, name: str) -> bool:
    subject = test.operand if isinstance(test, ast.UnaryOp) else test

    # x, not x, x is None, x is not None: the shapes a maybe-value is checked in
    if isinstance(subject, ast.Compare):
        is_none_check = (
            len(subject.ops) == 1
            and isinstance(subject.ops[0], ast.Is | ast.IsNot)
            and isinstance(subject.comparators[0], ast.Constant)
            and subject.comparators[0].value is None
        )
        subject = subject.left if is_none_check else subject

    return isinstance(subject, ast.Name) and subject.id == name


def is_simple_assign(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    )


def count_names(*nodes: ast.AST) -> Counter[str]:
    counts = Counter[str]()

    for node in nodes:
        for name in ast.walk(node):
            if isinstance(name, ast.Name):
                counts[name.id] += 1

    return counts
