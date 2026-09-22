import json
from pathlib import Path
import subprocess
import sys
from typing import Final

import pytest


CHECKER: Final = Path(__file__).with_name("check_linebreaks.py")
FOUR_LINES: Final = "First line\nSecond line\nThird line\nFourth line\n"


def run_checker(text: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--json"],
        input=text, capture_output=True, text=True, timeout=10, check=False,
    )


def test_accepts_standalone_four_line_paragraph() -> None:
    # Given / When
    completed = run_checker(FOUR_LINES)
    # Then
    assert completed.returncode == 0, completed.stdout
    assert completed.stderr == ""
    assert json.loads(completed.stdout)["issues"] == []
    assert json.loads(completed.stdout)["stats"]["paragraph_line_counts"] == [4]


@pytest.mark.parametrize("line_count", [1, 2, 3, 4, 5, 6])
@pytest.mark.parametrize("standalone", [True, False])
def test_paragraph_line_boundary(line_count: int, standalone: bool) -> None:
    # Given
    text = "Short line\n" * line_count
    if not standalone:
        text += "\nAnother paragraph\n"
    # When
    completed = run_checker(text)
    # Then
    if line_count <= 4:
        assert completed.returncode == 0, completed.stdout
        assert json.loads(completed.stdout)["issues"] == []
    else:
        assert completed.returncode == 1
        assert json.loads(completed.stdout)["issues"][0]["type"] == "paragraph_too_thick"
        assert json.loads(completed.stdout)["issues"][0]["paragraph"] == 1
        if standalone:
            assert json.loads(completed.stdout)["issues"][1]["type"] == "no_paragraph_break"


@pytest.mark.parametrize("length", [40, 41])
def test_line_character_boundary(length: int) -> None:
    # Given
    text = "가" * length
    # When
    completed = run_checker(text)
    # Then
    assert completed.returncode == (0 if length == 40 else 1)
    if length == 40:
        assert json.loads(completed.stdout)["issues"] == []
    else:
        assert json.loads(completed.stdout)["issues"][0]["type"] == "line_too_long"


@pytest.mark.parametrize("text, issue_type", [
    ("Body #tag", "hashtag_inline"),
    ("#tag\n\nBody", "hashtag_placement"),
    ("Body\n\n#tag", ""),
])
def test_hashtag_behavior(text: str, issue_type: str) -> None:
    # Given / When
    completed = run_checker(text)
    # Then
    assert completed.returncode == (1 if issue_type else 0)
    if issue_type:
        assert json.loads(completed.stdout)["issues"][0]["type"] == issue_type
    else:
        assert json.loads(completed.stdout)["issues"] == []
        assert json.loads(completed.stdout)["hints"][0]["line"] == 2


@pytest.mark.parametrize("text, has_hint", [
    ("앱을 쓰고, 다음 작업", True),
    ("앱을 쓰고,\n다음 작업", False),
    ("1,", True),
    ("1, 2", False),
])
def test_comma_hints_remain_advisory(text: str, has_hint: bool) -> None:
    # Given / When
    completed = run_checker(text)
    # Then
    assert completed.returncode == 0, completed.stdout
    assert json.loads(completed.stdout)["issues"] == []
    if has_hint:
        assert json.loads(completed.stdout)["hints"][0]["line"] == 1
    else:
        assert json.loads(completed.stdout)["hints"] == []
