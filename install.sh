#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
CODEX_AGENTS_FILE="${CODEX_AGENTS_FILE:-$HOME/.codex/AGENTS.md}"
ASIDE_SKILLS_DIR="${ASIDE_SKILLS_DIR:-$HOME/.aside/u/0/skills/user}"
START='<!-- threads-writing-skills -->'
END='<!-- /threads-writing-skills -->'
SKILLS="$(find "$REPO_DIR/skills" -mindepth 2 -maxdepth 2 -name SKILL.md -print | while IFS= read -r f; do basename "$(dirname "$f")"; done | LC_ALL=C sort)"

usage() { echo "Usage: $0 [--uninstall]"; echo "Discovers skills/*/SKILL.md at depth 2, sorted by name."; }
link_skills() {
  dir="$1"
  if [ ! -d "$(dirname "$dir")" ]; then echo "  건너뜀: 상위 폴더 없음 $(dirname "$dir")"; return; fi
  mkdir -p "$dir"
  for skill in $SKILLS; do
    target="$dir/$skill"; source="$REPO_DIR/skills/$skill"
    if [ -e "$target" ] && [ ! -L "$target" ]; then echo "  건너뜀: 비심링크 $target"; continue; fi
    ln -sfn "$source" "$target"; echo "  링크됨: $target -> $source"
  done
}
pointer_block() {
  printf '%s\n' "$START"
  for skill in $SKILLS; do printf '# SKILL: %s/skills/%s/SKILL.md\n' "$REPO_DIR" "$skill"; done
  printf '%s\n' "$END"
}
update_agents() {
  file="$1"; parent="$(dirname "$file")"
  if [ ! -d "$parent" ]; then echo "  건너뜀: 상위 폴더 없음 $parent"; return; fi
  tmp="$(mktemp "${TMPDIR:-/tmp}/threads-agents.XXXXXX")"
  if [ -f "$file" ]; then
    awk -v start="$START" -v end="$END" 'index($0,start){skip=1; next} index($0,end){skip=0; next} !skip{print}' "$file" > "$tmp"
  fi
  pointer_block >> "$tmp"
  mv "$tmp" "$file"
  echo "  갱신됨: $file"
}
remove_agents() {
  file="$1"; [ -f "$file" ] || return 0
  tmp="$(mktemp "${TMPDIR:-/tmp}/threads-agents.XXXXXX")"
  awk -v start="$START" -v end="$END" 'index($0,start){skip=1; next} index($0,end){skip=0; next} !skip{print}' "$file" > "$tmp"
  mv "$tmp" "$file"; echo "  마커 블록 제거됨: $file"
}
uninstall() {
  for dir in "$CLAUDE_SKILLS_DIR" "$ASIDE_SKILLS_DIR"; do
    for skill in $SKILLS; do target="$dir/$skill"; [ -L "$target" ] && rm "$target" && echo "  제거됨: $target"; done
  done
  remove_agents "$CODEX_AGENTS_FILE"
}

if [ "${1:-}" = "--help" ]; then usage; exit 0; fi
if [ "${1:-}" = "--uninstall" ]; then uninstall; exit 0; fi
if [ "$#" -gt 0 ]; then usage >&2; exit 2; fi
echo "저장소: $REPO_DIR"
link_skills "$CLAUDE_SKILLS_DIR"
update_agents "$CODEX_AGENTS_FILE"
link_skills "$ASIDE_SKILLS_DIR"
if command -v python3 >/dev/null 2>&1; then
  printf '짧은 줄.\n' | python3 "$REPO_DIR/skills/threads-linebreak/scripts/check_linebreaks.py" >/dev/null && echo "검사 스크립트 정상 동작"
else echo "python3 이 없어 검사 스크립트를 확인하지 못했다"; fi
echo "Claude Code·Codex·Aside를 새로 시작해야 스킬이 인식된다"
echo "인식 확인: Claude Code에서 /threads-writing-skills:threads-linebreak 또는 스킬 목록을 확인한다"
