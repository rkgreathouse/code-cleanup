from pathlib import Path

import pytest

from ..__main__ import main


def test_check_fails_and_leaves_messy_code_alone(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "a.py"
    path.write_text("x=1\n")

    exit_code = main([str(tmp_path), "--check"])

    assert exit_code == 1
    assert path.read_text() == "x=1\n"
    assert "a.py: would reformat" in capsys.readouterr().out


def test_fix_then_check_passes(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x=1\n")

    assert main([str(tmp_path)]) == 0
    assert main([str(tmp_path), "--check"]) == 0


def test_missing_root_exits_with_failure(tmp_path: Path) -> None:
    assert main([str(tmp_path / "missing")]) == 1


def test_unknown_report_is_a_usage_error(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as raised:
        main([str(tmp_path), "--report", "xml"])

    assert raised.value.code == 2
