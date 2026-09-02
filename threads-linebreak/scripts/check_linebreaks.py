#!/usr/bin/env python3
"""Threads 줄바꿈 패턴 검사기.

초안 텍스트를 읽어 규칙 위반과 분포를 보고한다.
판단이 필요한 항목(쉼표가 절 경계인지 나열인지)은 후보만 표시하고 결정은 사람에게 맡긴다.

    python3 check_linebreaks.py draft.txt
    cat draft.txt | python3 check_linebreaks.py
    python3 check_linebreaks.py draft.txt --json
"""

import argparse
import json
import re
import sys
from collections import Counter

MAX_LINE_CHARS = 40
MAX_PARAGRAPH_LINES = 3

# 절 경계 신호가 되는 연결어미. 이걸로 끝나는 쉼표는 줄바꿈 자리다.
# 실측 상위(-는데, -하고, -지만, -는지 …)를 포함하도록 어미 형태로 일반화했다.
CLAUSE_ENDING_RE = re.compile(
    r"(는데|인데|은데|지만|는지|던지|든지|거나|니라|라서|아서|어서|니까|면서|으며|이며|하며|고|며|서|면)$"
)

# 나열·수치 신호. 이걸로 끝나는 쉼표는 줄 중간에 두는 쪽이 자연스럽다.
LIST_PATTERN = re.compile(r"(\d|[A-Za-z]{1,4}|도|과|와|랑|이나)$")


def split_paragraphs(text):
    """빈 줄 1개 이상을 문단 경계로 본다."""
    paragraphs = []
    current = []
    for line in text.split("\n"):
        if line.strip() == "":
            if current:
                paragraphs.append(current)
                current = []
        else:
            current.append(line.rstrip())
    if current:
        paragraphs.append(current)
    return paragraphs


def classify_comma(fragment):
    """쉼표 앞 조각을 보고 절 경계/나열 중 무엇에 가까운지 추정한다."""
    stripped = fragment.rstrip()
    # 나열 신호를 먼저 본다. '11도,' 처럼 숫자+조사는 절 경계가 아니라 나열이다.
    if LIST_PATTERN.search(stripped):
        return "list"
    if CLAUSE_ENDING_RE.search(stripped):
        return "clause"
    return "unclear"


def analyze(text):
    paragraphs = split_paragraphs(text)
    lines = [line for para in paragraphs for line in para]

    issues = []
    hints = []

    # 규칙 위반: 긴 줄
    for idx, line in enumerate(lines, start=1):
        length = len(line)
        if length > MAX_LINE_CHARS:
            suggestion = ""
            if "," in line:
                head = line.split(",")[0]
                kind = classify_comma(head)
                if kind == "clause":
                    suggestion = f" — '{head[-12:]},' 뒤가 절 경계로 보인다. 여기서 끊어라"
                elif kind == "list":
                    suggestion = " — 쉼표가 나열이라 끊는 자리가 아니다. 연결어미를 찾아라"
            issues.append({
                "type": "line_too_long",
                "line": idx,
                "detail": f"{length}자 (기준 {MAX_LINE_CHARS}자){suggestion}",
                "text": line,
            })

    # 규칙 위반: 두꺼운 문단
    for idx, para in enumerate(paragraphs, start=1):
        if len(para) > MAX_PARAGRAPH_LINES:
            issues.append({
                "type": "paragraph_too_thick",
                "paragraph": idx,
                "detail": f"{len(para)}줄 (기준 {MAX_PARAGRAPH_LINES}줄) — 생각 단위로 쪼갤 자리를 찾아라",
                "text": para[0],
            })

    # 규칙 위반: 문단이 하나뿐
    if len(paragraphs) == 1 and len(lines) > 2:
        issues.append({
            "type": "no_paragraph_break",
            "detail": "빈 줄이 하나도 없다. 문단은 빈 줄 1개로 나눈다",
            "text": lines[0],
        })

    # 해시태그 위치 — 본문 줄에 섞여 있으면 마지막 단독 문단으로 빼야 한다
    for idx, line in enumerate(lines, start=1):
        if "#" in line and not line.strip().startswith("#"):
            issues.append({
                "type": "hashtag_inline",
                "line": idx,
                "detail": "해시태그가 본문 줄에 섞여 있다. 마지막에 단독 문단으로 빼라",
                "text": line,
            })

    tag_lines = [i for i, line in enumerate(lines, start=1) if line.strip().startswith("#")]
    if tag_lines:
        last_para = paragraphs[-1]
        tags_in_last_para_only = all(
            line.strip().startswith("#") for line in last_para
        ) and len(tag_lines) == len(last_para)
        if not tags_in_last_para_only:
            issues.append({
                "type": "hashtag_placement",
                "line": tag_lines[0],
                "detail": "해시태그는 마지막에 단독 문단으로 둔다",
                "text": lines[tag_lines[0] - 1],
            })

    # 해시태그를 붙였으면 의도인지 물어본다 — 기본은 0개다 (SKILL.md §5.6)
    if tag_lines:
        hints.append({
            "line": tag_lines[0],
            "detail": "해시태그가 있다. 기본 규칙은 0개다 — 150건 대조에서 조회 중앙 910(있음) vs 902(없음)로 차이가 없었다. 검색 유입을 노린 의도가 아니면 빼라",
            "text": lines[tag_lines[0] - 1],
        })

    # 판단이 필요한 쉼표 후보
    for idx, line in enumerate(lines, start=1):
        if line.rstrip().endswith(","):
            kind = classify_comma(line.rstrip()[:-1])
            if kind == "list":
                hints.append({
                    "line": idx,
                    "detail": "줄 끝 쉼표인데 나열처럼 보인다. 절 경계가 맞는지 확인하라",
                    "text": line,
                })
        else:
            for match in re.finditer(r"[^,]*,", line):
                fragment = match.group()[:-1]
                if classify_comma(fragment) == "clause":
                    hints.append({
                        "line": idx,
                        "detail": f"줄 중간 쉼표('{fragment[-10:]},')가 절 경계로 보인다. 여기서 줄을 바꿀지 보라",
                        "text": line,
                    })

    line_lengths = [len(line) for line in lines]
    endings = Counter(line[-1] for line in lines if line)
    comma_end = sum(1 for line in lines if line.rstrip().endswith(","))

    stats = {
        "paragraphs": len(paragraphs),
        "lines": len(lines),
        "chars_excluding_newlines": sum(line_lengths),
        "avg_line_chars": round(sum(line_lengths) / len(line_lengths), 1) if line_lengths else 0,
        "lines_over_limit": sum(1 for n in line_lengths if n > MAX_LINE_CHARS),
        "pct_lines_within_limit": round(
            100 * sum(1 for n in line_lengths if n <= MAX_LINE_CHARS) / len(line_lengths)
        ) if line_lengths else 0,
        "paragraph_line_counts": [len(p) for p in paragraphs],
        "pct_paragraphs_1_2_lines": round(
            100 * sum(1 for p in paragraphs if len(p) <= 2) / len(paragraphs)
        ) if paragraphs else 0,
        "line_end_chars": dict(endings.most_common(6)),
        "pct_lines_ending_comma": round(100 * comma_end / len(lines)) if lines else 0,
    }

    return {"stats": stats, "issues": issues, "hints": hints}


def render(result):
    stats = result["stats"]
    out = []
    out.append("── 분포 ──")
    out.append(
        f"문단 {stats['paragraphs']}개 · 줄 {stats['lines']}개 · "
        f"본문 {stats['chars_excluding_newlines']}자(줄바꿈 제외)"
    )
    out.append(
        f"줄 길이 평균 {stats['avg_line_chars']}자 · "
        f"{MAX_LINE_CHARS}자 이하 {stats['pct_lines_within_limit']}% (실측 기준 86%)"
    )
    out.append(
        f"문단 1~2줄 비율 {stats['pct_paragraphs_1_2_lines']}% (실측 기준 76%) · "
        f"구성 {stats['paragraph_line_counts']}"
    )
    out.append(
        f"줄 끝 쉼표 {stats['pct_lines_ending_comma']}% (실측 기준 9%, 절반 넘으면 과용)"
    )
    out.append(f"줄 끝 문자 {stats['line_end_chars']}")

    if result["issues"]:
        out.append("")
        out.append(f"── 고칠 것 {len(result['issues'])}건 ──")
        for issue in result["issues"]:
            where = (
                f"L{issue['line']}" if "line" in issue
                else f"문단{issue['paragraph']}" if "paragraph" in issue
                else "전체"
            )
            out.append(f"[{where}] {issue['detail']}")
            out.append(f"       {issue['text']}")
    else:
        out.append("")
        out.append("── 고칠 것 없음 ──")

    if result["hints"]:
        out.append("")
        out.append(f"── 확인해볼 것 {len(result['hints'])}건 (판단은 사람이) ──")
        for hint in result["hints"]:
            out.append(f"[L{hint['line']}] {hint['detail']}")
            out.append(f"       {hint['text']}")

    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(
        description="Threads 줄바꿈 패턴 검사기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "보고 항목:\n"
            "  위반 — 40자 초과 줄 / 3줄 초과 문단 / 해시태그 위치(마지막 줄이 아닌 곳)\n"
            "  분포 — 줄 길이 / 문단 길이 / 줄 끝 문자(쉼표·마침표 등)\n"
            "  판단 보류 — 줄 끝 쉼표는 연결어미인지 나열인지 문맥을 봐야 하므로 후보만 표시한다\n"
            "종료 코드: 0 = 위반 없음, 1 = 위반 있음 (SKILL.md 참조)"
        ),
    )
    parser.add_argument("path", nargs="?", help="검사할 텍스트 파일 (없으면 표준입력)")
    parser.add_argument("--json", action="store_true", help="JSON으로 출력")
    args = parser.parse_args()

    if args.path:
        with open(args.path, encoding="utf-8") as handle:
            text = handle.read()
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("입력이 비어 있다.", file=sys.stderr)
        return 1

    result = analyze(text)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render(result))
    return 1 if result["issues"] else 0


if __name__ == "__main__":
    sys.exit(main())
