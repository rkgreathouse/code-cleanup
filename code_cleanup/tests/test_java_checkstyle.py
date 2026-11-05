from pathlib import Path

from ..java.checkstyle import find_checkstyle_issues, group_by_file
from ..settings import load_settings


def test_reports_house_rules_against_the_cleaned_text(tmp_path: Path) -> None:
    settings = load_settings(tmp_path, None).java
    mirror = tmp_path / "mirror"
    copy = mirror / "A.java"
    copy.parent.mkdir()
    copy.write_text(
        "class A {\n  void f() {\n    try {\n      g();\n    } catch (Exception e) {\n"
        "      h();\n    }\n  }\n}\n"
    )

    findings = find_checkstyle_issues(mirror, tmp_path, [tmp_path / "A.java"], settings)

    assert [(item.code, item.line) for item in findings[tmp_path / "A.java"]] == [
        ("checkstyle:IllegalCatch", 5)
    ]


def test_maps_report_paths_back_to_the_project(tmp_path: Path) -> None:
    report = (
        f'<checkstyle><file name="{tmp_path}/src/A.java">'
        '<error line="3" column="7" severity="warning" message="m"'
        ' source="com.puppycrawl.tools.checkstyle.checks.coding.InnerAssignmentCheck"/>'
        "</file></checkstyle>"
    )

    findings = group_by_file(report, tmp_path, Path("/project"))

    assert [
        (item.code, item.line, item.column, item.is_error)
        for item in findings[Path("/project/src/A.java")]
    ] == [("checkstyle:InnerAssignment", 3, 7, False)]
