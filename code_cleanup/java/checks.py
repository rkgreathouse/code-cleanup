from tree_sitter import Node, Tree

from ..findings import Finding
from ..settings import JavaSettings
from .syntax import finding_at, has_modifier, text_of, walk

NESTING = {
    "if_statement",
    "for_statement",
    "enhanced_for_statement",
    "while_statement",
    "do_statement",
    "try_statement",
    "try_with_resources_statement",
    "switch_expression",
    "synchronized_statement",
}
STREAM_SOURCES = {
    "stream",
    "Stream",
    "IntStream",
    "LongStream",
    "DoubleStream",
    "Arrays",
}


def find_style_issues(tree: Tree, settings: JavaSettings) -> list[Finding]:
    findings = []

    for node in walk(tree.root_node):
        if node.type == "block_comment" and not settings.allow_javadoc:
            findings += find_javadoc(node)

        if not settings.allow_environment:
            findings += find_environment_reads(node)

        if node.type == "method_invocation" and settings.simple_streams:
            findings += find_tangled_streams(node)

        if node.type in ("method_declaration", "constructor_declaration"):
            findings += find_deep_nesting(node, settings.max_nesting)

    findings += find_extra_constants(tree, settings.max_class_constants)

    return findings


def find_javadoc(node: Node) -> list[Finding]:
    if not text_of(node).startswith("/**"):
        return []

    return [
        finding_at(
            node, "CC103", "Javadoc; let names and small methods carry the meaning"
        )
    ]


def find_environment_reads(node: Node) -> list[Finding]:
    if node.type == "method_invocation" and reads_environment(node):
        return [
            finding_at(
                node, "CC104", "reads the environment; bind it in application.yml"
            )
        ]

    is_annotation = node.type in ("annotation", "marker_annotation")

    if is_annotation and text_of(node.child_by_field_name("name")) == "Value":
        return [
            finding_at(
                node,
                "CC104",
                "@Value reads config piecemeal; bind it to a properties record",
            )
        ]

    return []


def reads_environment(node: Node) -> bool:
    owner = text_of(node.child_by_field_name("object"))
    name = text_of(node.child_by_field_name("name"))

    return owner == "System" and name in ("getenv", "getProperty", "getProperties")


def find_tangled_streams(node: Node) -> list[Finding]:

    # only the outermost call of a chain speaks for the chain
    if is_chained(node):
        return []

    names = set(chain_list(node))

    if not names & STREAM_SOURCES and not is_stream_source(node):
        return []

    steps = [name for name in chain_list(node) if name in ("map", "filter", "flatMap")]
    is_nested = any(contains_stream(argument) for argument in lambda_bodies(node))
    is_tangled = (
        steps.count("map") > 1 or steps.count("filter") > 1 or "flatMap" in steps
    )

    if not is_tangled and not is_nested:
        return []

    return [
        finding_at(
            node,
            "CC105",
            "stream with more than one map or filter, a flatMap, or a stream inside; "
            "use a loop or a helper",
        )
    ]


def is_chained(node: Node) -> bool:
    parent = node.parent
    return (
        parent is not None
        and parent.type == "method_invocation"
        and parent.child_by_field_name("object") == node
    )


def chain_list(node: Node) -> list[str]:
    names = []
    current: Node | None = node

    while current is not None and current.type == "method_invocation":
        names.append(text_of(current.child_by_field_name("name")))
        current = current.child_by_field_name("object")

    return names


def is_stream_source(node: Node) -> bool:
    current: Node | None = node

    while current is not None and current.type == "method_invocation":
        current = current.child_by_field_name("object")

    return text_of(current) in STREAM_SOURCES


def lambda_bodies(node: Node) -> list[Node]:
    bodies = []
    current: Node | None = node

    while current is not None and current.type == "method_invocation":
        arguments = current.child_by_field_name("arguments")
        bodies += [
            argument.child_by_field_name("body")
            for argument in (arguments.named_children if arguments else [])
            if argument.type == "lambda_expression"
        ]
        current = current.child_by_field_name("object")

    return [body for body in bodies if body is not None]


def contains_stream(node: Node) -> bool:
    return any(
        inner.type == "method_invocation"
        and text_of(inner.child_by_field_name("name")) == "stream"
        for inner in walk(node)
    )


def find_deep_nesting(method: Node, limit: int) -> list[Finding]:
    findings = []
    body = method.child_by_field_name("body")

    for node, depth in nested_blocks(body, 0):
        if depth == limit + 1:
            findings.append(
                finding_at(
                    node, "CC107", f"nested {depth} blocks deep, over {limit}; split it"
                )
            )

    return findings


def nested_blocks(node: Node | None, depth: int) -> list[tuple[Node, int]]:
    if node is None:
        return []

    found = []

    for child in node.named_children:
        # an else-if continues its if; a lambda or local class starts its own count
        is_else_if = child.type == "if_statement" and node.type == "if_statement"
        starts_over = child.type in ("lambda_expression", "class_body")
        counts = child.type in NESTING and not is_else_if
        inner = 0 if starts_over else depth + counts

        if counts and not starts_over:
            found.append((child, inner))

        found += nested_blocks(child, inner)

    return found


def find_extra_constants(tree: Tree, limit: int) -> list[Finding]:
    constants = [
        node
        for node in walk(tree.root_node)
        if node.type == "field_declaration" and is_constant(node)
    ]

    return [
        finding_at(
            node,
            "CC102",
            f"constant {number} of at most {limit}; move "
            f"{constant_name(node)} to application.yml",
        )
        for number, node in enumerate(constants, start=1)
        if number > limit
    ]


def is_constant(node: Node) -> bool:
    name = constant_name(node)

    return (
        has_modifier(node, "static") and has_modifier(node, "final") and name.isupper()
    )


def constant_name(node: Node) -> str:
    declarator = node.child_by_field_name("declarator")
    return text_of(declarator.child_by_field_name("name") if declarator else None)
