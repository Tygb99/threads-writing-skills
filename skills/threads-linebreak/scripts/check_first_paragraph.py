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
    line_count_ok = len(lines) <= MAX_FIRST_PARAGRAPH_LINES
    opening_ok = not first_line.endswith(SENTENCE_END)
    has_number = bool(re.search(r"\d", flat))
    has_quote = bool(re.search(r"[\"'“”‘’]", flat))
    return {
        "first_paragraph": paragraph,
        "first_line": first_line,
        "lines": len(lines),
        "chars": len(flat),
        "recommended_line_count": line_count_ok,
        "recommended_opening": opening_ok,
        "has_number": has_number,
        "has_quote": has_quote,
        "line_count": {
            "value": f"{len(lines)}줄",
            "verdict": "권장 범위" if line_count_ok else "3줄 이상 확인",
        },
        "opening": {
            "value": "미완결" if opening_ok else f"완결({first_line[-8:]})",
            "verdict": "미완결 권장" if opening_ok else "확인",
        },
        "number": {
            "value": "있음" if has_number else "없음",
            "verdict": "권장 충족" if has_number else "참고",
        },
        "quote": {
            "value": "있음" if has_quote else "없음",
            "verdict": "확인" if has_quote else "참고",
        },
    }


def report(result):
    return "\n".join([
        "── 첫 문단 검사 ──",
        result["first_paragraph"],
        "",
        f"첫 문단 줄 수: {result['line_count']['value']} · {result['line_count']['verdict']}",
        f"첫 줄 미완결: {result['opening']['value']} · {result['opening']['verdict']}",
        f"숫자 포함: {result['number']['value']} · {result['number']['verdict']}",
        f"따옴표 포함: {result['quote']['value']} · {result['quote']['verdict']}",
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
