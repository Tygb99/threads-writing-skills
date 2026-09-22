import importlib.util
import os
import subprocess
import sys
import unittest
from pathlib import Path


def _load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(f"{name}.py"))
    if spec is None or spec.loader is None:
        raise ImportError(name)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


jev_client = _load("jev_client")
check_linebreaks = _load("check_linebreaks")
check_first_paragraph = _load("check_first_paragraph")


class MarkCommasTests(unittest.TestCase):
    def test_marks_and_hides_linebreaks(self):
        state, metas = jev_client.mark_commas(["크롬 원격은 구글이 죽였고,", "2024년, 면접장"])
        self.assertEqual(state, "크롬 원격은 구글이 죽였고[,1] 2024년[,2] 면접장")
        self.assertNotIn("\n", state)
        self.assertEqual([m["at_line_end"] for m in metas], [True, False])
        self.assertEqual(metas[0]["fragment"], "크롬 원격은 구글이 죽였고")
        self.assertEqual(metas[1]["fragment"], "2024년")

    def test_missing_key_raises(self):
        env = os.environ.pop("AI_GATEWAY_API_KEY", None)
        try:
            with self.assertRaises(jev_client.JevUnavailable):
                jev_client.evaluate("x", {})
        finally:
            if env is not None:
                os.environ["AI_GATEWAY_API_KEY"] = env


class LinebreakJevTests(unittest.TestCase):
    def test_only_disagreements_sorted_by_confidence(self):
        text = "손을 쓸 수 없고,\n휠체어를 타고 다닌다\n\n2024년, 면접장에서\n3년, 4년을 적었다"

        def fake(lines):
            state, metas = jev_client.mark_commas(lines)
            out = []
            for m in metas:
                # 첫 문단 줄 끝 쉼표는 절 경계로 동의, 둘째 문단은 '2024년,'만 절 경계라고 우김
                choice = "clause" if (m["at_line_end"] or m["fragment"] == "2024년") else "list"
                conf = 0.9 if m["fragment"] == "2024년" else 0.3
                out.append({**m, "choice": choice, "p_clause": 0.5, "confidence": conf})
            return out

        result = check_linebreaks.analyze(text, jev_judge=fake)
        self.assertEqual(result["stats"]["jev"], {"asked": 3, "agree": 2, "disagree": 1})
        self.assertEqual(len(result["hints"]), 1)
        self.assertEqual(result["hints"][0]["line"], 3)
        self.assertIn("절 경계로 본다", result["hints"][0]["detail"])
        self.assertIn("Jev와 어긋난 쉼표", check_linebreaks.render(result))

    def test_without_jev_unchanged(self):
        result = check_linebreaks.analyze("본문\n\n#주제")
        self.assertNotIn("jev", result["stats"])

    def test_cli_exit_two_without_key(self):
        env = {k: v for k, v in os.environ.items() if k != "AI_GATEWAY_API_KEY"}
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("check_linebreaks.py")), "--jev"],
            input="짧은 글", text=True, capture_output=True, env=env,
        )
        self.assertEqual(proc.returncode, 2)


class FirstParagraphJevTests(unittest.TestCase):
    def test_jev_block_in_report(self):
        def fake(lines):
            return {"subject": "event", "subject_confidence": 0.8,
                    "subject_probabilities": {"event": 0.8, "artifact": 0.1, "other": 0.1},
                    "opening_incomplete_probability": 0.95}
        result = check_first_paragraph.analyze("오늘 아침 배포가 두 번 실패했고,\n원인은 환경변수였다", jev_judge=fake)
        self.assertEqual(result["jev"]["subject_ko"], "사건형")
        self.assertIn("Jev 주어 판정: 사건형 (confidence 0.80)", check_first_paragraph.report(result))

    def test_without_jev_keeps_human_line(self):
        result = check_first_paragraph.analyze("짧은 글")
        self.assertIsNone(result["jev"])
        self.assertTrue(check_first_paragraph.report(result).endswith("주어는 사람이 정한다"))


if __name__ == "__main__":
    unittest.main()
