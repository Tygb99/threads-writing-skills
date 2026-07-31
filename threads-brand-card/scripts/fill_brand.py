#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FIELDS = {
    "BRAND_NAME": "표시 이름",
    "BRAND_TAGLINE": "한 줄 소개",
    "BRAND_HANDLE": "핸들",
    "BRAND_LINK": "링크",
}
MARK_TOKEN = "BRAND_MARK_ABSOLUTE_PATH.png"


def read_brand(path: Path) -> dict[str, str]:
    if not path.exists():
        sys.exit(
            f"브랜드 파일이 없다: {path}\n"
            "사용자에게 표시 이름, 한 줄 소개, 핸들, 링크, 마크 이미지 경로를 물어 먼저 만들 것"
        )
    text = path.read_text()
    values: dict[str, str] = {}
    for token, label in FIELDS.items():
        m = re.search(r"\|\s*" + re.escape(label) + r"\s*\|\s*`([^`]+)`\s*\|", text)
        if not m:
            sys.exit(f"{path.name} 에서 `{label}` 행을 찾지 못했다")
        values[token] = m.group(1).replace("\\|", "|")

    mark = re.search(r"```\n(.+\.png)\n```", text)
    if not mark:
        sys.exit(f"{path.name} 에서 마크 이미지 경로 코드블록을 찾지 못했다")
    mark_path = Path(mark.group(1))
    if not mark_path.exists():
        sys.exit(f"마크 이미지가 없다: {mark_path}")
    values[MARK_TOKEN] = str(mark_path)
    return values


def main() -> None:
    here = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(
        description="brand.local.md 값으로 카드 템플릿의 플레이스홀더를 채운다"
    )
    ap.add_argument("output")
    ap.add_argument("--template", default=str(here / "assets/brand-card-template.html"))
    ap.add_argument("--brand", default=str(here / "brand.local.md"))
    args = ap.parse_args()

    values = read_brand(Path(args.brand))
    html = Path(args.template).read_text()
    for token, value in values.items():
        html = html.replace(token, value)

    leftover = re.findall(r"BRAND_[A-Z_]+", html)
    if leftover:
        sys.exit(f"치환되지 않은 플레이스홀더: {sorted(set(leftover))}")

    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    print(f"filled={out}")
    for token, value in values.items():
        print(f"{token}={value}")


if __name__ == "__main__":
    main()
