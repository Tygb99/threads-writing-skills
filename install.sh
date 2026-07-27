#!/usr/bin/env bash
# threads-writing-skills 설치 — 링크만 걸고 아무것도 복사·삭제하지 않는다.
# 이후 저장소에서 git pull 하면 Claude Code와 Codex 양쪽이 함께 갱신된다.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS=(threads-linebreak threads-web-publish alt-text-generator)

CLAUDE_SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
CODEX_AGENTS_FILE="${CODEX_AGENTS_FILE:-$HOME/.codex/AGENTS.md}"
MARKER="<!-- threads-writing-skills -->"

echo "저장소: $REPO_DIR"
echo

# 1. Claude Code — ~/.claude/skills 에 심볼릭 링크
if [ -d "$(dirname "$CLAUDE_SKILLS_DIR")" ]; then
  mkdir -p "$CLAUDE_SKILLS_DIR"
  for skill in "${SKILLS[@]}"; do
    target="$CLAUDE_SKILLS_DIR/$skill"
    if [ -e "$target" ] && [ ! -L "$target" ]; then
      echo "  건너뜀: $target 이 이미 있고 심볼릭 링크가 아니다. 직접 확인할 것"
      continue
    fi
    ln -sfn "$REPO_DIR/$skill" "$target"
    echo "  링크됨: $target -> $REPO_DIR/$skill"
  done
else
  echo "  Claude Code 설정 폴더($(dirname "$CLAUDE_SKILLS_DIR"))가 없어 건너뜀"
fi
echo

# 2. Codex — 전역 AGENTS.md 에 스킬 경로 한 줄
if [ -d "$(dirname "$CODEX_AGENTS_FILE")" ]; then
  if grep -qF "$MARKER" "$CODEX_AGENTS_FILE" 2>/dev/null; then
    echo "  이미 등록됨: $CODEX_AGENTS_FILE"
  else
    {
      printf '\n%s\n' "$MARKER"
      printf '# SKILL: Threads(스레드) 글의 줄바꿈·문단을 다듬거나 검사할 때는 `%s/threads-linebreak/SKILL.md`를 먼저 읽고 그 규칙을 따르세요.\n' "$REPO_DIR"
      printf '# SKILL: Threads 웹을 브라우저 자동화로 조작해 글을 올리거나 예약·수정할 때는 `%s/threads-web-publish/SKILL.md`를 먼저 읽고 그 절차를 따르세요.\n' "$REPO_DIR"
      printf '# SKILL: 이미지의 한국어 대체 텍스트(alt text)를 만들 때는 `%s/alt-text-generator/SKILL.md`를 먼저 읽고 그 형식을 따르세요.\n' "$REPO_DIR"
    } >> "$CODEX_AGENTS_FILE"
    echo "  등록됨: $CODEX_AGENTS_FILE"
  fi
else
  echo "  Codex 설정 폴더($(dirname "$CODEX_AGENTS_FILE"))가 없어 건너뜀"
fi
echo

# 3. 검사 스크립트 동작 확인
if command -v python3 >/dev/null 2>&1; then
  printf '짧은 줄.\n\n두 번째 문단.\n' | python3 "$REPO_DIR/threads-linebreak/scripts/check_linebreaks.py" >/dev/null \
    && echo "검사 스크립트 정상 동작"
else
  echo "python3 이 없어 검사 스크립트를 확인하지 못했다"
fi

echo
echo "완료. Claude Code나 Codex를 새로 시작하면 스킬이 잡힌다."
