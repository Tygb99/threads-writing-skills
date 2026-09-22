import json
import subprocess
import sys
import unittest
from pathlib import Path

import importlib.util

_SPEC = importlib.util.spec_from_file_location("check_first_paragraph", Path(__file__).with_name("check_first_paragraph.py"))
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("check_first_paragraph 모듈을 불러올 수 없다")
check_first_paragraph = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(check_first_paragraph)


class FirstParagraphTests(unittest.TestCase):
    def test_four_shape_items(self):
        result = check_first_paragraph.analyze('오늘 3시에 "배포가')
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["lines"], 1)
        self.assertTrue(result["recommended_opening"])
        self.assertTrue(result["has_number"])
        self.assertTrue(result["has_quote"])
        self.assertEqual(result["number"], {"value": "있음", "verdict": "권장 충족"})
        self.assertEqual(result["quote"], {"value": "있음", "verdict": "확인"})

    def test_three_lines_exit_one(self):
        proc = subprocess.run([sys.executable, str(Path(__file__).with_name("check_first_paragraph.py"))], input="a\nb\nc", text=True, capture_output=True)
        self.assertEqual(proc.returncode, 1)

    def test_json_has_only_shape_fields(self):
        proc = subprocess.run([sys.executable, str(Path(__file__).with_name("check_first_paragraph.py")), "--json"], input="한 줄", text=True, capture_output=True)
        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertNotIn("subject", data)
        self.assertIn("has_quote", data)
        self.assertIn("value", data["number"])
        self.assertIn("verdict", data["number"])


if __name__ == "__main__":
    unittest.main()
