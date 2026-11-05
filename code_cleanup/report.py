import json
from xml.etree import ElementTree

from .findings import FileResult


def render_report(results: list[FileResult], style: str, check: bool) -> str:
    if style == "json":
        return render_json(results)

    if style == "junit":
        return render_junit(results, check)

    return render_text(results, check)


def render_text(results: list[FileResult], check: bool) -> str:
    lines = []
    change = "would reformat" if check else "reformatted"

    for result in results:
        if result.is_changed:
            lines.append(f"{result.path}: {change}")

        lines += [
            f"{result.path}:{finding.line}:{finding.column}: {finding.code} "
            f"{finding.message}{'' if finding.is_error else ' (warning)'}"
            for finding in result.findings
        ]

    lines.append(summarize(results, change))

    return "\n".join(lines)


def summarize(results: list[FileResult], change: str) -> str:
    changed = sum(result.is_changed for result in results)
    findings = [finding for result in results for finding in result.findings]
    errors = sum(finding.is_error for finding in findings)
    warnings = len(findings) - errors

    return (
        f"{len(results)} files checked, {changed} {change}, "
        f"{errors} errors, {warnings} warnings"
    )


def render_json(results: list[FileResult]) -> str:
    entries = [
        {
            "path": result.path.as_posix(),
            "language": result.language,
            "changed": result.is_changed,
            "findings": [
                {
                    "line": finding.line,
                    "column": finding.column,
                    "code": finding.code,
                    "message": finding.message,
                    "severity": "error" if finding.is_error else "warning",
                }
                for finding in result.findings
            ],
        }
        for result in results
    ]

    return json.dumps(entries, indent=2)


def render_junit(results: list[FileResult], check: bool) -> str:
    suite = ElementTree.Element(
        "testsuite", name="code-cleanup", tests=str(len(results))
    )
    failures = 0

    for result in results:
        case = ElementTree.SubElement(
            suite, "testcase", classname=result.language, name=result.path.as_posix()
        )
        problems = [
            f"{finding.line}:{finding.column}: {finding.code} {finding.message}"
            for finding in result.findings
            if finding.is_error
        ]

        if result.is_changed and check:
            problems.insert(0, "would reformat")

        if problems:
            failures += 1
            failure = ElementTree.SubElement(case, "failure", message=problems[0])
            failure.text = "\n".join(problems)

    suite.set("failures", str(failures))

    return ElementTree.tostring(suite, encoding="unicode", xml_declaration=True)


def is_failure(results: list[FileResult], check: bool) -> bool:
    has_errors = any(
        finding.is_error for result in results for finding in result.findings
    )
    has_changes = check and any(result.is_changed for result in results)

    return has_errors or has_changes
