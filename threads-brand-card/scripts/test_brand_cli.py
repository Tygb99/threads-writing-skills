from __future__ import annotations

import base64
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
PIXEL = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGM4+yoKAASZAhLAtuVlAAAAAElFTkSuQmCC"
)


class BrandCliTests(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.mark = self.root / "mark.png"
        self.mark.write_bytes(PIXEL)
        self.brand = self.root / "brand.local.md"
        self.brand.write_text(
            (SKILL / "brand.local.example.md").read_text(encoding="utf-8").replace(
                "/absolute/path/to/brand-mark.png", str(self.mark)
            ),
            encoding="utf-8",
        )
        self.card = self.root / "card.html"

    def test_example_fills_every_template(self) -> None:
        templates = [SKILL / "assets/brand-card-template.html"]
        templates.extend(sorted((SKILL / "assets/themes").glob("*.html")))
        self.assertEqual(len(templates), 8)
        for template in templates:
            with self.subTest(template=template.name):
                result = subprocess.run(
                    [sys.executable, str(SKILL / "scripts/fill_brand.py"), str(self.card),
                     "--brand", str(self.brand), "--template", str(template)],
                    capture_output=True, text=True, check=False, timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                filled = self.card.read_text(encoding="utf-8")
                self.assertNotIn("BRAND_", filled)
                self.assertIn("예시 브랜드", filled)
                self.assertIn(str(self.mark), filled)

    def test_brand_text_is_escaped_and_default_uses_forest_press(self) -> None:
        self.brand.write_text(
            self.brand.read_text(encoding="utf-8").replace("예시 브랜드", "<기록> & 나\\|너"),
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(SKILL / "scripts/fill_brand.py"), str(self.card),
             "--brand", str(self.brand)],
            cwd=self.root, capture_output=True, text=True, check=False, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        filled = self.card.read_text(encoding="utf-8")
        self.assertIn("&lt;기록&gt; &amp; 나|너", filled)
        self.assertIn("#10201a", filled)

    def test_relative_mark_is_rejected(self) -> None:
        self.brand.write_text(
            self.brand.read_text(encoding="utf-8").replace(str(self.mark), "mark.png"),
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(SKILL / "scripts/fill_brand.py"), str(self.card),
             "--brand", str(self.brand)],
            cwd=self.root, capture_output=True, text=True, check=False, timeout=10,
        )
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.card.exists())

    def test_render_validates_current_output_before_replacing_existing_png(self) -> None:
        self.card.write_text("<!doctype html><p>카드</p>", encoding="utf-8")
        output = self.root / "card.png"
        chrome = self.root / "chrome-fixture"
        cases = (
            ("timeout_without_png", "import time; time.sleep(30)", 1),
            ("timeout_with_png", "target.write_bytes(pixel)\nimport time; time.sleep(30)", 0),
            ("wrong_size", "target.write_bytes(pixel[:16] + bytes.fromhex('0000000200000002') + pixel[24:])", 1),
            ("truncated_png", "target.write_bytes(pixel[:12])", 1),
            ("chrome_failure", "raise SystemExit(7)", 1),
        )
        for name, action, code in cases:
            with self.subTest(case=name):
                output.write_bytes(PIXEL)
                chrome.write_text(
                    f"#!{sys.executable}\nimport sys\nfrom pathlib import Path\n"
                    "target = Path(next(arg.split('=', 1)[1] for arg in sys.argv if arg.startswith('--screenshot=')))\n"
                    f"pixel = {PIXEL!r}\n{action}\n",
                    encoding="utf-8",
                )
                chrome.chmod(0o755)
                result = subprocess.run(
                    [sys.executable, str(SKILL / "scripts/render_brand_card.py"),
                     str(self.card), str(output), "--chrome", str(chrome),
                     "--width", "1", "--height", "1", "--timeout", "1"],
                    capture_output=True, text=True, check=False, timeout=10,
                )
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertEqual(output.read_bytes(), PIXEL)


if __name__ == "__main__":
    unittest.main()
