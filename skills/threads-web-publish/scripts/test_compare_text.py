import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("compare_text.py")


def compare_files(
    expected: bytes, actual: bytes, options: tuple[str, ...] = ()
) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as directory:
        expected_path = Path(directory) / "expected.txt"
        actual_path = Path(directory) / "actual.txt"
        expected_path.write_bytes(expected)
        actual_path.write_bytes(actual)
        return subprocess.run(
            [sys.executable, str(SCRIPT), *options, str(expected_path), str(actual_path)],
            capture_output=True,
            text=True,
            check=False,
        )


class CompareTextTests(unittest.TestCase):
    def test_help_exits_successfully(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--rstrip-actual", result.stdout)

    def test_exact_comparison_including_line_endings(self) -> None:
        cases = (
            ("한글\n같은 글\n", "한글\n같은 글\n", 0, "첫 차이: 없음"),
            ("", "", 0, "첫 차이: 없음"),
            ("코드가", "드코가", 1, "인덱스 0"),
            ("가\n나다", "가\n너다", 1, "2행 1열"),
            ("안녕", "안", 1, "인덱스 1"),
            ("안", "안녕", 1, "인덱스 1"),
            ("가\r\n", "가\n", 1, "인덱스 1"),
            ("가", "가", 1, "인덱스 0"),
            ("가", "가\n", 1, "인덱스 1"),
        )
        for expected, actual, code, location in cases:
            with self.subTest(expected=expected, actual=actual):
                result = compare_files(expected.encode(), actual.encode())
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertIn(location, result.stdout)

    def test_trimming_is_explicit_and_only_affects_actual(self) -> None:
        cases = (
            ("가", "가 \n\t", 0),
            ("가\n", "가\n", 1),
            (" 가", "가", 1),
            ("가\n나", "가 나\n", 1),
        )
        for expected, actual, code in cases:
            with self.subTest(expected=expected, actual=actual):
                result = compare_files(
                    expected.encode(), actual.encode(), ("--rstrip-actual",)
                )
                self.assertEqual(result.returncode, code, result.stderr)

    def test_invalid_utf8_is_an_input_error(self) -> None:
        result = compare_files(b"text", b"\xff")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)

    def test_missing_file_is_an_input_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            absent = str(Path(directory) / "absent.txt")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), absent, absent],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
