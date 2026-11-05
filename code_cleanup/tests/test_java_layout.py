from pathlib import Path

from ..findings import Finding
from ..java.layout import find_service_issues

MAIN = "src/main/java/com/example/shop"
SERVICE = {
    f"{MAIN}/Application.java": """package com.example.shop;

@SpringBootApplication
public class Application {
  public static void main(String[] args) {
    SpringApplication.run(Application.class, args);
  }
}
""",
    f"{MAIN}/errors/ApiException.java": """package com.example.shop.errors;

public abstract class ApiException extends RuntimeException {}
""",
    f"{MAIN}/errors/ErrorHandler.java": """package com.example.shop.errors;

@RestControllerAdvice
public class ErrorHandler {
  public ProblemDetail handle(ApiException error) { return null; }
}
""",
    f"{MAIN}/order/OrderController.java": """package com.example.shop.order;

@RestController
public class OrderController {
  private final OrderService service;

  public Order get(long id) { return service.find(id); }
}
""",
    "src/test/java/com/example/shop/ApplicationTest.java": "",
    "src/test/java/com/example/shop/errors/ErrorHandlerTest.java": "",
    "src/test/java/com/example/shop/order/OrderControllerTest.java": "",
    "src/main/resources/log4j2-spring.xml": "<Configuration><JsonTemplateLayout/>\n",
    "src/main/resources/application.yml": "shop: {}\n",
    "pom.xml": "<project/>\n",
}


def make_service(root: Path) -> dict[Path, str]:
    for name, text in SERVICE.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    return {
        root / name: text for name, text in SERVICE.items() if name.endswith(".java")
    }


def codes(root: Path, texts: dict[Path, str]) -> dict[str, list[str]]:
    issues = find_service_issues(root, texts)
    return {str(path.relative_to(root)): to_codes(issues[path]) for path in issues}


def to_codes(findings: list[Finding]) -> list[str]:
    return [finding.code for finding in findings]


def test_accepts_the_house_service_layout(tmp_path: Path) -> None:
    assert codes(tmp_path, make_service(tmp_path)) == {}


def test_reports_a_class_with_methods_but_no_test(tmp_path: Path) -> None:
    texts = make_service(tmp_path)
    test = "src/test/java/com/example/shop/order/OrderControllerTest.java"
    (tmp_path / test).unlink()

    assert codes(tmp_path, texts) == {f"{MAIN}/order/OrderController.java": ["CC302"]}


def test_reports_sources_outside_the_maven_layout(tmp_path: Path) -> None:
    texts = make_service(tmp_path)
    texts[tmp_path / "scripts" / "Tool.java"] = "class Tool {}\n"

    assert codes(tmp_path, texts) == {"scripts/Tool.java": ["CC301"]}


def test_reports_an_entry_class_that_does_more_than_start(tmp_path: Path) -> None:
    texts = make_service(tmp_path)
    entry = tmp_path / MAIN / "Application.java"
    texts[entry] = texts[entry].replace(
        "  public static void main",
        "  @Bean Clock clock() { return null; }\n  public static void main",
    )

    assert codes(tmp_path, texts) == {f"{MAIN}/Application.java": ["CC303"]}


def test_reports_a_missing_errors_package(tmp_path: Path) -> None:
    texts = make_service(tmp_path)
    del texts[tmp_path / MAIN / "errors" / "ErrorHandler.java"]

    assert codes(tmp_path, texts) == {"pom.xml": ["CC304"]}


def test_reports_reaching_into_another_feature(tmp_path: Path) -> None:
    texts = make_service(tmp_path)
    texts[tmp_path / MAIN / "cart" / "Cart.java"] = (
        "package com.example.shop.cart;\n\n"
        "import com.example.shop.order.OrderController;\n\n"
        "public record Cart(long id) {}\n"
    )

    assert codes(tmp_path, texts) == {f"{MAIN}/cart/Cart.java": ["CC305"]}


def test_reports_a_controller_using_a_repository(tmp_path: Path) -> None:
    texts = make_service(tmp_path)
    controller = tmp_path / MAIN / "order" / "OrderController.java"
    texts[controller] = texts[controller].replace(
        "OrderService service", "OrderRepository repository"
    )

    assert codes(tmp_path, texts) == {f"{MAIN}/order/OrderController.java": ["CC306"]}


def test_reports_plain_text_logs_and_properties_files(tmp_path: Path) -> None:
    texts = make_service(tmp_path)
    resources = tmp_path / "src" / "main" / "resources"
    (resources / "log4j2-spring.xml").write_text("<Configuration/>\n")
    (resources / "application.yml").unlink()
    (resources / "application.properties").write_text("a=1\n")

    assert codes(tmp_path, texts) == {
        "pom.xml": ["CC203", "CC402"],
        "src/main/resources/application.properties": ["CC402"],
    }
