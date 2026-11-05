import json
from pathlib import Path
from xml.etree import ElementTree

from ..findings import FileResult, Finding
from ..report import is_failure, render_report


def make_results() -> list[FileResult]:
    warning = Finding(line=1, column=1, code="CC001", message="long", is_error=False)
    error = Finding(line=3, column=5, code="T201", message="print", is_error=True)

    return [
        FileResult(Path("a.py"), "python", is_changed=True, findings=(warning,)),
        FileResult(Path("b.py"), "python", is_changed=False, findings=(error,)),
    ]


def test_text_lists_changes_findings_and_a_summary() -> None:
    assert render_report(make_results(), "text", check=True).splitlines() == [
        "a.py: would reformat",
        "a.py:1:1: CC001 long (warning)",
        "b.py:3:5: T201 print",
        "2 files checked, 1 would reformat, 1 errors, 1 warnings",
    ]


def test_json_keeps_severity() -> None:
    entries = json.loads(render_report(make_results(), "json", check=True))

    assert entries[0]["findings"][0]["severity"] == "warning"


def test_junit_fails_changed_files_only_in_check_mode() -> None:
    checked = ElementTree.fromstring(render_report(make_results(), "junit", check=True))
    fixed = ElementTree.fromstring(render_report(make_results(), "junit", check=False))

    assert checked.get("failures") == "2"
    assert fixed.get("failures") == "1"


def test_warnings_alone_do_not_fail() -> None:
    results = make_results()[:1]

    assert not is_failure(results, check=False)
    assert is_failure(results, check=True)
