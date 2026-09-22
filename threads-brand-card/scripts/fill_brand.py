#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
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
    if not path.is_file():
        sys.exit(
            f"브랜드 파일이 없다: {path}\n"
            "이 스킬 폴더의 brand.local.example.md를 brand.local.md로 복사한다.\n"
            "사용자에게 표시 이름, 한 줄 소개, 핸들, 링크, 마크 PNG의 절대 경로를 물어 채운다."
        )
    text = path.read_text(encoding="utf-8")
    values: dict[str, str] = {}
    for token, label in FIELDS.items():
        m = re.search(
            r"^\|[ \t]*" + re.escape(label) + r"[ \t]*\|[ \t]*`([^`\n]+)`[ \t]*\|[ \t]*$",
            text, re.MULTILINE,
        )
        if not m:
            sys.exit(f"{path.name} 에서 `{label}` 행을 찾지 못했다")
        values[token] = m.group(1).replace("\\|", "|")

    mark = re.search(r"^```\n([^\n]+\.png)\n```[ \t]*$", text, re.MULTILINE)
    if not mark:
        sys.exit(f"{path.name} 에서 마크 이미지 경로 코드블록을 찾지 못했다")
    mark_path = Path(mark.group(1))
    if not mark_path.is_absolute():
        sys.exit(f"마크 이미지 경로는 절대 경로여야 한다: {mark_path}")
    if not mark_path.is_file():
        sys.exit(f"마크 이미지가 없다: {mark_path}")
    values[MARK_TOKEN] = str(mark_path)
    return values


def main() -> None:
    here = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(
        description="브랜드 견본 형식의 Markdown으로 카드 HTML의 BRAND_*를 채운다. Python 3.9+ 표준 라이브러리만 사용한다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""입력 형식:
  brand.local.example.md를 복사해 작성한다. UTF-8 표의 항목은
  표시 이름, 한 줄 소개, 핸들, 링크이며 각 값은 백틱으로 감싼다.
  값 안의 세로줄은 \\|로 쓴다. 백틱과 줄바꿈은 값에 넣지 않는다.
  마크 경로는 언어 표시 없는 코드블록 한 줄에 적는 절대 .png 경로다.

파일 접근:
  --brand와 --template의 파일만 읽고 마크 파일의 존재를 확인한다.
  기본 경로의 시작점은 현재 작업 폴더가 아닌 이 스킬 폴더다.
  폴더 재귀 탐색, 패턴 검색, 정렬은 하지 않는다.
  출력 부모 폴더를 만들며 같은 이름의 HTML은 덮어쓴다.

출력: stdout에 filled=<절대 HTML 경로>와 치환한 BRAND_*=<값>을 출력한다.
종료 코드: 0 성공/도움말, 1 파일·형식·미치환 토큰 오류, 2 CLI 인자 오류.
""",
    )
    ap.add_argument("output", help="채운 HTML을 저장할 경로")
    ap.add_argument(
        "--template", default=str(here / "assets/themes/theme-06-forest-press.html"),
        help="입력 HTML (기본: 이 스킬 폴더의 assets/themes/theme-06-forest-press.html)",
    )
    ap.add_argument("--brand", default=str(here / "brand.local.md"), help="브랜드 Markdown (기본: 이 스킬 폴더의 brand.local.md)")
    args = ap.parse_args()

    values = read_brand(Path(args.brand))
    template = Path(args.template).read_text(encoding="utf-8")
    for token, value in values.items():
        template = template.replace(token, html.escape(value, quote=True))

    leftover = re.findall(r"BRAND_[A-Z_]+", template)
    if leftover:
        sys.exit(f"치환되지 않은 플레이스홀더: {sorted(set(leftover))}")

    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(template, encoding="utf-8")
    print(f"filled={out}")
    for token, value in values.items():
        print(f"{token}={value}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, UnicodeError) as error:
        sys.exit(f"파일 처리 실패: {error}")
