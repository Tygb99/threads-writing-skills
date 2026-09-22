#!/usr/bin/env python3
"""Jev(TypeSafe System One) 판정 클라이언트. 표준 라이브러리만 쓴다.

Vercel AI Gateway의 `/v1/evaluate`로 쉼표 종류·첫 문단 주어를 판정한다.
문장을 생성하지 않고 선택지별 확률과 confidence만 돌려주므로, 검사기는 이 값을
"사람이 볼 순서"를 정하는 데만 쓰고 최종 판단은 여전히 사람에게 둔다.

환경변수 `AI_GATEWAY_API_KEY`가 필요하다. 키가 없으면 `JevUnavailable`을 던진다.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request

ENDPOINT = os.environ.get("JEV_ENDPOINT", "https://ai-gateway.vercel.sh/v1/evaluate")
MODEL = os.environ.get("JEV_MODEL", "typesafe-ai/jev")
TIMEOUT_SEC = 60
RETRIES = 6  # 업스트림 429(high demand)가 잦다. 지수 백오프로 버틴다.

COMMA_INSTRUCTIONS = (
    "Threads 게시물의 한 문단이다. 표시된 쉼표 [,N]이 무엇을 잇는지 고르라. "
    "쉼표 바로 앞 어절이 용언의 연결어미(-는데, -하고, -지만, -면서, -라서, -니까, -고, -며, -는지, -면 등)로 끝나면 clause다. "
    "같은 연결어미가 반복되는 병렬 절(예: '~했고, ~했고, ~했다' / '~인지, ~인지')도 각각 clause다. "
    "쉼표 앞이 명사·숫자·날짜·시각·조사로 끝나는 항목 나열, 짧은 동격, 영문 약어, 감탄·대답('아니요,')이면 list다."
)
COMMA_CRITERIA = {
    "clause": "절 경계 쉼표. 연결어미 뒤에서 다음 절이 새 줄에서 시작하는 자리",
    "list": "나열·수치·동격 쉼표. 줄 중간에 두는 자리",
}

SUBJECT_INSTRUCTIONS = (
    "Threads 게시물의 첫 문단이다. 첫 문단의 주어(화제)가 무엇인지 고르라. "
    "글쓴이가 겪은 사건·상황·사고·발견·대화가 앞에 서면 event, "
    "글쓴이가 만든 앱·책·스킬·이미지·기능 같은 산출물이 앞에 서면 artifact, "
    "질문·의견·정보 전달처럼 둘 다 아니면 other다."
)
SUBJECT_CRITERIA = {
    "event": "사건형. 일어난 일·상황·대화가 주어",
    "artifact": "작업물형. 만든 것·결과물이 주어",
    "other": "기타. 질문·주장·정보",
}
OPENING_INSTRUCTIONS = (
    "Threads 게시물의 첫 줄이다. 이 줄이 문장 중간에서 끊겨 다음 줄로 이어지는 미완결 형태인가? "
    "종결어미(-다, -요, -죠, -까)나 마침표·물음표로 끝나 한 문장이 완결되면 false다."
)


class JevUnavailable(RuntimeError):
    """키가 없거나 요청이 끝내 실패했을 때."""


def _key() -> str:
    key = os.environ.get("AI_GATEWAY_API_KEY", "").strip()
    if not key:
        raise JevUnavailable("AI_GATEWAY_API_KEY가 없다. Vercel AI Gateway 키를 환경변수로 넘겨라")
    return key


def evaluate(state, questions: dict) -> dict:
    """`/v1/evaluate` 한 번 호출. answers dict를 돌려준다."""
    key = _key()
    body = json.dumps({"model": MODEL, "state": state, "questions": questions}).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    last = "unknown"
    for attempt in range(RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data.get("answers", {})
        except urllib.error.HTTPError as exc:
            last = f"HTTP {exc.code}"
            if exc.code not in (429, 500, 502, 503, 504):
                raise JevUnavailable(f"Jev 요청 실패: {last}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:  # 네트워크
            last = str(exc)
        if attempt < RETRIES:
            time.sleep(min(2 ** attempt, 20))
    raise JevUnavailable(f"Jev 요청이 계속 실패했다: {last}")


def mark_commas(paragraph_lines: list[str]) -> tuple[str, list[dict]]:
    """문단의 줄을 이어 붙이고 쉼표마다 [,N] 표식을 단다.

    줄바꿈은 지운다(모델이 실제 줄바꿈 위치를 보면 판정이 아니라 베끼기가 된다).
    돌려주는 목록의 각 항목은 {n, line(1-based), at_line_end, fragment}.
    """
    marked, metas, n = [], [], 0
    for li, line in enumerate(paragraph_lines, start=1):
        out = ""
        for ci, ch in enumerate(line):
            if ch == ",":
                n += 1
                out += f"[,{n}]"
                before = re.sub(r"\[,\d+\]", ",", out[:-len(f"[,{n}]")]).split(",")[-1]
                metas.append({
                    "n": n,
                    "line": li,
                    "at_line_end": ci == len(line.rstrip()) - 1,
                    "fragment": before.strip(),
                })
            else:
                out += ch
        marked.append(out)
    return " ".join(marked), metas


def judge_commas(paragraph_lines: list[str]) -> list[dict]:
    """문단 안 모든 쉼표를 한 번의 요청으로 판정한다.

    각 항목: {n, line, at_line_end, fragment, choice, p_clause, confidence}.
    숫자 사이 쉼표(1,000)는 자명하므로 묻지 않고 제외한다.
    """
    state, metas = mark_commas(paragraph_lines)
    ask = [m for m in metas if not re.search(rf"\d\[,{m['n']}\]\d", state)]
    if not ask:
        return []
    questions = {
        f"c{m['n']}": {
            "type": "choice",
            "instructions": COMMA_INSTRUCTIONS.replace("[,N]", f"[,{m['n']}]"),
            "criteria": COMMA_CRITERIA,
        }
        for m in ask
    }
    answers = evaluate(state, questions)
    out = []
    for m in ask:
        a = answers.get(f"c{m['n']}") or {}
        probs = a.get("probabilities") or {}
        out.append({
            **m,
            "choice": a.get("choice"),
            "p_clause": probs.get("clause"),
            "confidence": a.get("confidence"),
        })
    return out


def judge_first_paragraph(paragraph_lines: list[str]) -> dict:
    """첫 문단 주어 유형(event/artifact/other)과 첫 줄 미완결 여부를 판정한다."""
    state = {"first_paragraph": " ".join(l.strip() for l in paragraph_lines), "first_line": paragraph_lines[0].strip()}
    questions = {
        "subject": {"type": "choice", "instructions": SUBJECT_INSTRUCTIONS, "criteria": SUBJECT_CRITERIA},
        "opening_incomplete": {"type": "boolean", "instructions": OPENING_INSTRUCTIONS},
    }
    answers = evaluate(state, questions)
    subj = answers.get("subject") or {}
    opening = answers.get("opening_incomplete") or {}
    return {
        "subject": subj.get("choice"),
        "subject_probabilities": subj.get("probabilities"),
        "subject_confidence": subj.get("confidence"),
        "opening_incomplete_probability": opening.get("probability"),
    }
