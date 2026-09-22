#!/usr/bin/env python3
"""첫 문단의 형태를 점검하는 표준 라이브러리 검사기."""

import argparse
import json
import re
import sys

MAX_FIRST_PARAGRAPH_LINES = 2
SENTENCE_END = (".", "!", "?", "…", "다", "요", "죠", "까")


def first_paragraph(text):
    lines = []
    for line in text.splitlines():
        if not line.strip():
            if lines:
                break
            continue
        lines.append(line.rstrip())
    return lines


def analyze(text):
    lines = first_paragraph(text)
    if not lines:
        return None
    paragraph = "\n".join(lines)
    flat = paragraph.replace("\n", "")
    first_line = lines[0].strip()
    return {
        "first_paragraph": paragraph,
        "first_line": first_line,
        "lines": len(lines),
        "chars": len(flat),
        "recommended_line_count": len(lines) <= MAX_FIRST_PARAGRAPH_LINES,
        "recommended_opening": not first_line.endswith(SENTENCE_END),
        "has_number": bool(re.search(r"\d", flat)),
        "has_quote": bool(re.search(r"[\"'“”‘’]", flat)),
    }


def report(result):
    opening = "권장" if result["recommended_opening"] else "확인"
    count = "권장" if result["recommended_line_count"] else "확인"
    number = "확인" if result["has_number"] else "권장"
    quote = "확인" if result["has_quote"] else "권장"
    return "\n".join([
        "── 첫 문단 검사 ──",
        result["first_paragraph"],
        "",
        f"첫 문단 줄 수: {result['lines']}줄 · {count} (1~2줄)",
        f"첫 줄 미완결: {opening}",
        f"숫자 포함: {number}",
        f"따옴표 포함: {quote}",
        "주어는 사람이 정한다",
    ])


def main():
    parser = argparse.ArgumentParser(description="Threads 첫 문단 형태 검사기")
    parser.add_argument("path", nargs="?", help="검사할 텍스트 파일 (없으면 표준입력)")
    parser.add_argument("--json", action="store_true", help="JSON으로 출력")
    args = parser.parse_args()
    text = open(args.path, encoding="utf-8").read() if args.path else sys.stdin.read()
    result = analyze(text)
    if result is None:
        print("본문이 비어 있다.", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else report(result))
    return 1 if len(first_paragraph(text)) >= 3 else 0


if __name__ == "__main__":
    sys.exit(main())
