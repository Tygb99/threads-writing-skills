#!/usr/bin/env python3
"""첫 문단의 형태를 점검하는 표준 라이브러리 검사기.

`--jev`를 주면 주어 유형(사건형/작업물형/기타)과 첫 줄 미완결 여부를 Jev에게 묻는다.
주어 판정은 참고값이며 최종 판단은 사람이 한다. AI_GATEWAY_API_KEY가 필요하다.
"""

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


SUBJECT_KO = {"event": "사건형", "artifact": "작업물형", "other": "기타"}


def analyze(text, jev_judge=None):
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
    jev = None
    if jev_judge is not None:
        j = jev_judge(lines)
        jev = {
            "subject": j.get("subject"),
            "subject_ko": SUBJECT_KO.get(j.get("subject") or "", "미확인"),
            "subject_confidence": j.get("subject_confidence"),
            "subject_probabilities": j.get("subject_probabilities"),
            "opening_incomplete_probability": j.get("opening_incomplete_probability"),
        }
    return {
        "jev": jev,
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
    lines = [
        "── 첫 문단 검사 ──",
        result["first_paragraph"],
        "",
        f"첫 문단 줄 수: {result['line_count']['value']} · {result['line_count']['verdict']}",
        f"첫 줄 미완결: {result['opening']['value']} · {result['opening']['verdict']}",
        f"숫자 포함: {result['number']['value']} · {result['number']['verdict']}",
        f"따옴표 포함: {result['quote']['value']} · {result['quote']['verdict']}",
    ]
    jev = result.get("jev")
    if jev:
        conf = jev.get("subject_confidence")
        p_open = jev.get("opening_incomplete_probability")
        conf_s = f"{conf:.2f}" if isinstance(conf, (int, float)) else "-"
        open_s = f"{p_open:.2f}" if isinstance(p_open, (int, float)) else "-"
        lines.append(f"Jev 주어 판정: {jev['subject_ko']} (confidence {conf_s}) · 첫 줄 미완결 확률 {open_s}")
        lines.append("주어는 사람이 정한다. Jev 값은 참고다")
    else:
        lines.append("주어는 사람이 정한다")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Threads 첫 문단 형태 검사기")
    parser.add_argument("path", nargs="?", help="검사할 텍스트 파일 (없으면 표준입력)")
    parser.add_argument("--json", action="store_true", help="JSON으로 출력")
    parser.add_argument("--jev", action="store_true", help="주어 유형·미완결을 Jev에 묻는다. AI_GATEWAY_API_KEY 필요")
    args = parser.parse_args()
    judge = None
    if args.jev:
        try:
            import jev_client
        except ImportError:
            print("jev_client.py가 같은 폴더에 없다.", file=sys.stderr)
            return 2
        if not jev_client.os.environ.get("AI_GATEWAY_API_KEY"):
            print("AI_GATEWAY_API_KEY가 없다. --jev를 쓰려면 Vercel AI Gateway 키를 환경변수로 넘겨라.", file=sys.stderr)
            return 2
        judge = jev_client.judge_first_paragraph
    text = open(args.path, encoding="utf-8").read() if args.path else sys.stdin.read()
    try:
        result = analyze(text, jev_judge=judge)
    except Exception as exc:  # noqa: BLE001 - Jev 실패는 검사를 막지 않는다
        if judge is None:
            raise
        print(f"Jev 판정 실패, 형태 검사만 출력한다: {exc}", file=sys.stderr)
        result = analyze(text)
    if result is None:
        print("본문이 비어 있다.", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else report(result))
    return 1 if len(first_paragraph(text)) >= 3 else 0


if __name__ == "__main__":
    sys.exit(main())
