import json
import subprocess
import sys
import unittest

import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location("check_linebreaks", Path(__file__).with_name("check_linebreaks.py"))
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("check_linebreaks 모듈을 불러올 수 없다")
check_linebreaks = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(check_linebreaks)


class LinebreakTests(unittest.TestCase):
    def test_line_length_boundary(self):
        self.assertEqual(check_linebreaks.analyze("가" * 40)["issues"], [])
        self.assertTrue(check_linebreaks.analyze("가" * 41)["issues"])

    def test_paragraph_boundary(self):
        good = "\n".join(["가"] * 4)
        bad = "\n".join(["가"] * 5)
        self.assertFalse(any(i["type"] == "paragraph_too_thick" for i in check_linebreaks.analyze(good)["issues"]))
        self.assertTrue(any(i["type"] == "paragraph_too_thick" for i in check_linebreaks.analyze(bad)["issues"]))

    def test_hashtag_location(self):
        result = check_linebreaks.analyze("본문\n\n#주제")
        self.assertFalse(any(i["type"] == "hashtag_placement" for i in result["issues"]))
        result = check_linebreaks.analyze("본문 #주제")
        self.assertTrue(any(i["type"] == "hashtag_inline" for i in result["issues"]))

    def test_empty_input_exit_one(self):
        proc = subprocess.run([sys.executable, str(Path(__file__).with_name("check_linebreaks.py"))], input="\n", text=True, capture_output=True)
        self.assertEqual(proc.returncode, 1)

    def test_json_structure(self):
        proc = subprocess.run([sys.executable, str(Path(__file__).with_name("check_linebreaks.py")), "--json"], input="짧은 글", text=True, capture_output=True)
        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertEqual(set(data), {"stats", "issues", "hints"})


if __name__ == "__main__":
    unittest.main()
