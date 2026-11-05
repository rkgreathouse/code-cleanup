from tree_sitter import Node, Tree

from ..findings import Finding
from ..settings import JavaSettings
from .syntax import finding_at, has_modifier, text_of, walk

LOG_LEVELS = {"trace", "debug", "info", "warn", "error"}
LOGGING_BACKENDS = (
    "org.apache.logging.log4j.core",
    "ch.qos.logback",
    "java.util.logging",
)


def find_logging_issues(tree: Tree, settings: JavaSettings) -> list[Finding]:
    if not settings.logging_checks:
        return []

    findings = []

    for node in walk(tree.root_node):
        if node.type == "import_declaration":
            findings += find_backend_import(node)

        if node.type == "field_declaration" and declares_logger(node):
            findings += find_logger_shape(node)

        if node.type == "method_invocation" and is_log_call(node):
            findings += find_built_message(node)

    return findings


def find_backend_import(node: Node) -> list[Finding]:
    imported = text_of(node).removeprefix("import").removeprefix(" static").strip()

    if not imported.startswith(LOGGING_BACKENDS):
        return []

    return [
        finding_at(
            node,
            "CC201",
            "configures logging in code; log4j2-spring.xml holds the setup, code logs "
            "through SLF4J",
        )
    ]


def declares_logger(node: Node) -> bool:
    declarator = node.child_by_field_name("declarator")
    value = declarator.child_by_field_name("value") if declarator else None

    return value is not None and text_of(value).split("(")[0].endswith(
        ("LoggerFactory.getLogger", "LogManager.getLogger")
    )


def find_logger_shape(node: Node) -> list[Finding]:
    declarator = node.child_by_field_name("declarator")
    name = text_of(declarator.child_by_field_name("name") if declarator else None)
    value = text_of(declarator.child_by_field_name("value") if declarator else None)
    owner = enclosing_class(node)
    expected = f"LoggerFactory.getLogger({owner}.class)"
    is_private_constant = all(
        has_modifier(node, keyword) for keyword in ("private", "static", "final")
    )

    if name == "log" and is_private_constant and value == expected:
        return []

    return [
        finding_at(
            node,
            "CC202",
            f"logger must be: private static final Logger log = {expected};",
        )
    ]


def enclosing_class(node: Node) -> str:
    current = node.parent
    kinds = ("class_declaration", "record_declaration", "enum_declaration")

    while current is not None and current.type not in kinds:
        current = current.parent

    return text_of(current.child_by_field_name("name")) if current else ""


def is_log_call(node: Node) -> bool:
    owner = text_of(node.child_by_field_name("object"))
    name = text_of(node.child_by_field_name("name"))

    return owner == "log" and name in LOG_LEVELS


def find_built_message(node: Node) -> list[Finding]:
    arguments = node.child_by_field_name("arguments")
    message = (
        arguments.named_children[0] if arguments and arguments.named_children else None
    )

    if message is None or not is_built(message):
        return []

    return [
        finding_at(
            message,
            "CC204",
            "log message built eagerly; pass a constant with {} placeholders and the "
            "values as arguments",
        )
    ]


def is_built(node: Node) -> bool:
    if node.type == "binary_expression":
        return text_of(node.child_by_field_name("operator")) == "+"

    if node.type == "method_invocation":
        return text_of(node.child_by_field_name("name")) in ("format", "formatted")

    return node.type == "template_expression"
