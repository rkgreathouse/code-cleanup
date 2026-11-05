from pathlib import Path

from ..findings import FileResult, Finding, all_findings, group_by_path


def make_finding(code: str) -> Finding:
    return Finding(line=1, column=1, code=code, message="", is_error=True)


def test_groups_findings_by_path_keeping_their_order() -> None:
    first, second, third = make_finding("A"), make_finding("B"), make_finding("C")
    issues = [(Path("a"), first), (Path("b"), second), (Path("a"), third)]

    assert group_by_path(issues) == {Path("a"): [first, third], Path("b"): [second]}


def test_flattens_findings_across_results() -> None:
    finding = make_finding("A")
    results = [
        FileResult(Path("a"), "python", False, (finding,)),
        FileResult(Path("b"), "python", False, (finding, finding)),
    ]

    assert len(all_findings(results)) == 3
