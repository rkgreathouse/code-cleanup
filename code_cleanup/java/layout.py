from dataclasses import dataclass
from pathlib import Path

from tree_sitter import Node

from ..findings import Finding
from .maven import group_by_module
from .syntax import annotation_names, finding_at, parse_java, text_of, walk

TYPES = (
    "class_declaration",
    "record_declaration",
    "enum_declaration",
    "interface_declaration",
)
WIRING = {"Configuration", "ConfigurationProperties"}


@dataclass(frozen=True, slots=True)
class JavaType:
    path: Path
    node: Node
    package: str
    name: str
    annotations: frozenset[str]
    method_count: int
    imports: tuple[str, ...]
    is_main: bool


def find_service_issues(
    root: Path, texts: dict[Path, str]
) -> dict[Path, list[Finding]]:
    issues: dict[Path, list[Finding]] = {}

    for module, paths in group_by_module(root, sorted(texts)).items():
        types = read_module_types(module, paths, texts)
        found = [
            *find_misplaced_files(module, paths),
            *find_untested_types(module, types),
            *find_entry_issues(module, types),
            *find_error_issues(module, types),
            *find_feature_imports(types),
            *find_controller_repositories(types),
            *find_config_issues(module),
        ]

        for path, finding in found:
            issues[path] = [*issues.get(path, []), finding]

    return issues


def read_module_types(
    module: Path, paths: list[Path], texts: dict[Path, str]
) -> list[JavaType]:
    types = []

    for path in paths:
        types += read_types(module, path, texts[path])

    return types


def read_types(module: Path, path: Path, text: str) -> list[JavaType]:
    tree = parse_java(text)
    package = next(
        (
            text_of(node.named_children[0])
            for node in tree.root_node.named_children
            if node.type == "package_declaration" and node.named_children
        ),
        "",
    )
    imports = tuple(
        text_of(node).removeprefix("import").strip().rstrip(";").strip()
        for node in tree.root_node.named_children
        if node.type == "import_declaration"
    )

    return [
        JavaType(
            path=path,
            node=node,
            package=package,
            name=text_of(node.child_by_field_name("name")),
            annotations=frozenset(annotation_names(node)),
            method_count=count_methods(node),
            imports=imports,
            is_main=path.is_relative_to(module / "src" / "main" / "java"),
        )
        for node in tree.root_node.named_children
        if node.type in TYPES
    ]


def count_methods(node: Node) -> int:
    body = node.child_by_field_name("body")
    members = body.named_children if body else []

    return sum(member.type == "method_declaration" for member in members)


def find_misplaced_files(module: Path, paths: list[Path]) -> list[tuple[Path, Finding]]:
    roots = [module / "src" / "main" / "java", module / "src" / "test" / "java"]

    message = "outside src/main/java and src/test/java"

    return [
        (path, Finding(1, 1, "CC301", message, True))
        for path in paths
        if not is_under_any(path, roots)
    ]


def is_under_any(path: Path, folders: list[Path]) -> bool:
    return any(path.is_relative_to(folder) for folder in folders)


def find_untested_types(
    module: Path, types: list[JavaType]
) -> list[tuple[Path, Finding]]:
    tests = module / "src" / "test" / "java"
    found = []

    for item in types:
        test = tests / package_path(item.package) / f"{item.name}Test.java"

        # wiring classes hold no logic of their own; the application test covers them
        if not item.is_main or not item.method_count or item.annotations & WIRING:
            continue

        if not test.is_file():
            message = f"{item.name} has methods but no {item.name}Test"
            found.append((item.path, finding_at(item.node, "CC302", message)))

    return found


def package_path(package: str) -> Path:
    return Path(*package.split(".")) if package else Path()


def find_entry_issues(
    module: Path, types: list[JavaType]
) -> list[tuple[Path, Finding]]:
    entries = [item for item in types if "SpringBootApplication" in item.annotations]

    if len(entries) != 1:
        message = f"needs one @SpringBootApplication class, found {len(entries)}"
        return [(module / "pom.xml", Finding(1, 1, "CC303", message, True))]

    entry = entries[0]
    root_package = entry.package
    misplaced = [
        item
        for item in types
        if item.is_main and not f"{item.package}.".startswith(f"{root_package}.")
    ]
    found = [
        (
            item.path,
            finding_at(item.node, "CC303", f"outside the root package {root_package}"),
        )
        for item in misplaced
    ]

    if entry.name != "Application" or not has_entry_shape(entry.node):
        message = (
            "entry class shape: class Application with only "
            "main(String[] args) { SpringApplication.run(Application.class, args); }"
        )
        found.append((entry.path, finding_at(entry.node, "CC303", message)))

    return found


def has_entry_shape(node: Node) -> bool:
    body = node.child_by_field_name("body")
    members = [
        member for member in (body.named_children if body else []) if member.is_named
    ]
    methods = [member for member in members if member.type == "method_declaration"]

    if len(members) != 1 or len(methods) != 1:
        return False

    method = methods[0]
    statements = method.child_by_field_name("body")
    calls = (
        [text_of(statement) for statement in statements.named_children]
        if statements
        else []
    )

    return text_of(method.child_by_field_name("name")) == "main" and calls == [
        "SpringApplication.run(Application.class, args);"
    ]


def find_error_issues(
    module: Path, types: list[JavaType]
) -> list[tuple[Path, Finding]]:
    errors = [
        item for item in types if item.is_main and item.package.endswith(".errors")
    ]
    has_handler = any("RestControllerAdvice" in item.annotations for item in errors)
    has_base = any(extends(item.node) == "RuntimeException" for item in errors)

    if has_handler and has_base:
        return []

    message = (
        "needs an errors package with an exception base extending RuntimeException "
        "and one @RestControllerAdvice that maps exceptions to responses"
    )
    return [(module / "pom.xml", Finding(1, 1, "CC304", message, True))]


def extends(node: Node) -> str:
    superclass = node.child_by_field_name("superclass")
    return (
        text_of(superclass.named_children[0])
        if superclass and superclass.named_children
        else ""
    )


def find_feature_imports(types: list[JavaType]) -> list[tuple[Path, Finding]]:
    packages = {item.package for item in types}
    found = []

    for item in types:
        for imported in item.imports:
            owner, _, name = imported.rpartition(".")
            is_internal = name.endswith(("Controller", "Repository"))

            # a feature reaches another feature through its service, never around it
            if is_internal and owner in packages and owner != item.package:
                message = f"imports {name} from another feature; go through its service"
                found.append((item.path, finding_at(item.node, "CC305", message)))

    return found


def find_controller_repositories(types: list[JavaType]) -> list[tuple[Path, Finding]]:
    found = []

    for item in types:
        if not item.annotations & {"RestController", "Controller"}:
            continue

        if (repository := find_repository(item.node)) is not None:
            message = "controller uses a repository; call a service"
            found.append((item.path, finding_at(repository, "CC306", message)))

    return found


def find_repository(node: Node) -> Node | None:
    return next(
        (
            inner
            for inner in walk(node)
            if inner.type == "type_identifier" and text_of(inner).endswith("Repository")
        ),
        None,
    )


def find_config_issues(module: Path) -> list[tuple[Path, Finding]]:
    resources = module / "src" / "main" / "resources"
    log_config = resources / "log4j2-spring.xml"
    found = []

    if not log_config.is_file() or "JsonTemplateLayout" not in log_config.read_text():
        message = "needs src/main/resources/log4j2-spring.xml with a JsonTemplateLayout"
        found.append((module / "pom.xml", Finding(1, 1, "CC203", message, True)))

    if (resources / "application.properties").is_file():
        message = "settings belong in application.yml"
        found.append(
            (
                resources / "application.properties",
                Finding(1, 1, "CC402", message, True),
            )
        )

    if not (resources / "application.yml").is_file():
        message = "needs src/main/resources/application.yml"
        found.append((module / "pom.xml", Finding(1, 1, "CC402", message, True)))

    return found
