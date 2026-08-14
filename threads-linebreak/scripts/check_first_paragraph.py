#!/usr/bin/env python3
"""Threads 첫 문단 검사기.

첫 문단만 떼어 읽고, 도달과 상관이 확인된 항목을 점검한다.
판단이 갈리는 항목(주어가 사건인지 작업물인지)은 근거를 보여주고 결정은 사람에게 맡긴다.

    python3 check_first_paragraph.py draft.txt
    cat draft.txt | python3 check_first_paragraph.py
    python3 check_first_paragraph.py draft.txt --json

기준은 @yong_____jjang 계정 실측이다 — 2026년 4~8월, 공식 Threads API,
발행 24시간이 지난 최상위 글 129건. 조회는 전부 중앙값이다.

    첫 문단의 주어      사건형 940 · 기타 866 · 작업물형 207
    첫 문단 줄 수       1줄 878 · 2줄 933 · 3줄 이상 565
    첫 줄 미완결        미완결 914 · 완결 746
    숫자                있음 927 · 없음 705
    따옴표              있음 936 · 없음 826
    첫 문단 글자 수     상관 없음 (20자든 60자든 차이가 없었다)

어휘 난이도(낯선 낱말)는 단독으로는 도달을 설명하지 못했다 —
낯선 낱말이 든 글의 중앙값이 오히려 높았다(1,409 vs 799).
그래서 낱말은 감점 항목이 아니라 **주어 판정의 참고 자료**로만 보여준다.
"""

import argparse
import json
import re
import sys

MAX_FIRST_PARAGRAPH_LINES = 2

# 밖에서 벌어진 일 — 첫 문단의 주어가 사건이라는 신호
EVENT_RE = re.compile(
    # '만들었'의 '들었'처럼 작업 동사 안에 사건 낱말이 박혀 오탐이 난다 — 앞 글자를 막아둔다.
    r"(다녀왔|(?<!만)났다|끊겼|도전|댓글|전화|만났|받았|(?<!다녀)왔다|생겼|(?<!만)들었|봤다|물었"
    r"|걸렸|당했|열렸|갔다|샀다|잃었|떨어졌|막혔|터졌)"
)

# 내가 만들거나 고친 것 — 주어가 작업물이라는 신호
ARTIFACT_RE = re.compile(
    r"(만들었|공개합니다|공개한다|정리했|올립니다|지웠|깎|붙였|바꿨|추가했|업데이트|고쳤|출시|배포|런칭|완성)"
)

# 설명이 필요한 낱말. 감점이 아니라 참고용으로 표시한다.
JARGON = [
    "스킬", "크레딧", "토큰", "API", "프롬프트", "파이프라인", "스크립트", "커밋", "레포",
    "세션", "에이전트", "컨텍스트", "인스턴스", "디버깅", "리팩터", "쿼리", "SDK", "CLI",
    "MCP", "LLM", "워크플로", "자동화", "사용량", "알고리즘", "오픈소스",
]

SENTENCE_END = (".", "!", "?", "…")


def first_paragraph(text):
    """빈 줄 1개 이상을 문단 경계로 보고 첫 문단만 돌려준다."""
    lines = []
    for line in text.split("\n"):
        if line.strip() == "":
            if lines:
                break
            continue
        lines.append(line.rstrip())
    return lines


def classify_subject(paragraph):
    """첫 문단의 주어가 사건인지 작업물인지 가른다. 확신이 없으면 '판단 필요'다."""
    event = EVENT_RE.findall(paragraph)
    artifact = ARTIFACT_RE.findall(paragraph)
    if event and not artifact:
        return "사건", event, artifact
    if artifact and not event:
        return "작업물", event, artifact
    if event and artifact:
        return "혼합", event, artifact
    return "판단 필요", event, artifact


def analyze(text):
    lines = first_paragraph(text)
    if not lines:
        return None
    paragraph = "\n".join(lines)
    flat = paragraph.replace("\n", "")
    first_line = lines[0].strip()
    subject, event_hits, artifact_hits = classify_subject(paragraph)

    return {
        "first_paragraph": paragraph,
        "first_line": first_line,
        "lines": len(lines),
        "chars": len(flat),
        "subject": subject,
        "event_signals": event_hits,
        "artifact_signals": artifact_hits,
        "open_ended": not first_line.endswith(SENTENCE_END),
        "has_number": bool(re.search(r"\d", flat)),
        "has_quote": bool(re.search(r"[\"'“”‘’]", flat)),
        "jargon": [w for w in JARGON if w in paragraph],
    }


def report(result):
    out = []
    out.append("── 첫 문단 ──")
    out.append(result["first_paragraph"])
    out.append("")
    out.append(f"{result['lines']}줄 · {result['chars']}자")
    out.append("")

    problems = []
    notes = []

    if result["subject"] == "작업물":
        problems.append(
            "주어가 **작업물**이다 (실측 중앙값 207 vs 사건형 940). "
            f"신호: {', '.join(result['artifact_signals'])}\n"
            "       → 만든 것 말고, 그것을 만들게 된 사건으로 열어라."
        )
    elif result["subject"] == "사건":
        notes.append(f"주어가 사건이다 (신호: {', '.join(result['event_signals'])}). 가장 잘 나온 유형이다.")
    elif result["subject"] == "혼합":
        notes.append("사건과 작업이 섞였다. 사건 쪽을 앞으로 보내면 더 낫다.")
    else:
        notes.append("주어가 사건인지 작업물인지 기계로는 못 갈랐다. 직접 판단하라 — "
                     "밖에서 벌어진 일이면 통과, 내가 만든 것이면 다시 써라.")

    if result["lines"] > MAX_FIRST_PARAGRAPH_LINES:
        problems.append(f"첫 문단이 {result['lines']}줄이다 (3줄 이상 565 vs 1~2줄 878~933). → 쪼개라.")

    if not result["open_ended"]:
        problems.append("첫 줄이 마침표로 끝난다 (완결 746 vs 미완결 914). → 문장을 다음 줄로 넘겨라.")

    if not result["has_number"]:
        notes.append("숫자가 없다 (있음 927 vs 없음 705). 넣을 수 있으면 넣어라.")

    if result["jargon"]:
        notes.append(
            f"설명이 필요한 낱말: {', '.join(result['jargon'])} — 감점은 아니다. "
            "다만 이 낱말이 '내가 만든 것' 이야기를 끌고 오는지 확인하라."
        )

    if problems:
        out.append(f"── 고칠 것 {len(problems)}건 ──")
        out += [f"[{i}] {p}" for i, p in enumerate(problems, 1)]
    else:
        out.append("── 고칠 것 없음 ──")

    if notes:
        out.append("")
        out.append("── 참고 ──")
        out += [f"· {n}" for n in notes]

    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description="Threads 첫 문단 검사기")
    parser.add_argument("path", nargs="?", help="초안 파일. 생략하면 표준 입력을 읽는다.")
    parser.add_argument("--json", action="store_true", help="기계가 읽는 형식으로 출력")
    args = parser.parse_args()

    text = open(args.path, encoding="utf-8").read() if args.path else sys.stdin.read()
    result = analyze(text)
    if result is None:
        print("본문이 비어 있다.", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(report(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
