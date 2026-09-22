#!/usr/bin/env bash
# threads-writing-skills 설치 — 심링크만 건다. 복사·삭제하지 않는다.
# 대상: Claude Code(~/.claude/skills), Codex(~/.codex/skills), Aside(~/.aside/u/0/skills/user)
# 스킬 탐색: skills/*/SKILL.md 깊이 2, LC_ALL=C 이름순. 심링크는 따라가지 않는다.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
CODEX_SKILLS_DIR="${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"
ASIDE_SKILLS_DIR="${ASIDE_SKILLS_DIR:-$HOME/.aside/u/0/skills/user}"
# 구판 install.sh가 ~/.codex/AGENTS.md에 남긴 포인터 블록. 있으면 지운다.
LEGACY_AGENTS_FILE="${CODEX_AGENTS_FILE:-$HOME/.codex/AGENTS.md}"
START='<!-- threads-writing-skills -->'
END='<!-- /threads-writing-skills -->'
SKILLS="$(find "$REPO_DIR/skills" -mindepth 2 -maxdepth 2 -name SKILL.md -print | while IFS= read -r f; do basename "$(dirname "$f")"; done | LC_ALL=C sort)"

usage() {
  echo "Usage: $0 [--uninstall]"
  echo "skills/*/SKILL.md(깊이 2, 이름순)를 찾아 세 곳에 심링크를 건다:"
  echo "  CLAUDE_SKILLS_DIR=$CLAUDE_SKILLS_DIR"
  echo "  CODEX_SKILLS_DIR=$CODEX_SKILLS_DIR"
  echo "  ASIDE_SKILLS_DIR=$ASIDE_SKILLS_DIR"
  echo "환경변수로 경로를 바꿀 수 있다. 상위 폴더가 없는 대상은 건너뛴다."
}
link_skills() {
  dir="$1"
  if [ ! -d "$(dirname "$dir")" ]; then echo "  건너뜀: 상위 폴더 없음 $(dirname "$dir")"; return; fi
  mkdir -p "$dir"
  for skill in $SKILLS; do
    target="$dir/$skill"; source="$REPO_DIR/skills/$skill"
    if [ -e "$target" ] && [ ! -L "$target" ]; then echo "  건너뜀: 심링크가 아닌 항목이 이미 있음 $target (직접 확인할 것)"; continue; fi
    ln -sfn "$source" "$target"; echo "  링크됨: $target -> $source"
  done
}
unlink_skills() {
  dir="$1"
  for skill in $SKILLS; do
    target="$dir/$skill"
    if [ -L "$target" ]; then rm "$target"; echo "  제거됨: $target"; fi
  done
}
remove_legacy_block() {
  file="$1"
  [ -f "$file" ] || return 0
  grep -qF "$START" "$file" || return 0
  tmp="$(mktemp "${TMPDIR:-/tmp}/threads-agents.XXXXXX")"
  awk -v start="$START" -v end="$END" 'index($0,start){skip=1; next} index($0,end){skip=0; next} !skip{print}' "$file" > "$tmp"
  mv "$tmp" "$file"; echo "  구판 포인터 블록 제거됨: $file"
}

if [ "${1:-}" = "--help" ]; then usage; exit 0; fi
if [ "${1:-}" = "--uninstall" ]; then
  for dir in "$CLAUDE_SKILLS_DIR" "$CODEX_SKILLS_DIR" "$ASIDE_SKILLS_DIR"; do unlink_skills "$dir"; done
  remove_legacy_block "$LEGACY_AGENTS_FILE"
  exit 0
fi
if [ "$#" -gt 0 ]; then usage >&2; exit 2; fi

echo "저장소: $REPO_DIR"
echo "Claude Code:"; link_skills "$CLAUDE_SKILLS_DIR"
echo "Codex:";      link_skills "$CODEX_SKILLS_DIR"
echo "Aside:";      link_skills "$ASIDE_SKILLS_DIR"
remove_legacy_block "$LEGACY_AGENTS_FILE"
if command -v python3 >/dev/null 2>&1; then
  printf '짧은 줄.\n' | python3 "$REPO_DIR/skills/threads-linebreak/scripts/check_linebreaks.py" >/dev/null && echo "검사 스크립트 정상 동작"
else echo "python3 이 없어 검사 스크립트를 확인하지 못했다"; fi
echo "Claude Code·Codex·Aside를 새로 시작해야 스킬이 인식된다"
echo "인식 확인: Claude Code는 /threads-linebreak 등 스킬 목록, Codex는 \$threads-linebreak 멘션이나 /skills 목록, Aside는 aside skills list"
