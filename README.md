# threads-writing-skills

Measured Korean writing skills for Threads, based on 397 captions and self-replies from four months of official Threads API reports. The rules are measured rather than guessed: 397 posts were counted line by line. The same skills are distributed as Claude Code and Codex plugins, with an install script for Aside.

![Same post, different line breaks](assets/before-after.png)

Both sides are 152 characters; line breaks change reading speed, not length.

## Skills

| Skill | Description |
|---|---|
| [`threads-linebreak`](skills/threads-linebreak/) | Shapes Korean Threads line breaks and checks drafts |
| [`threads-web-publish`](skills/threads-web-publish/) | Publishes, schedules, edits, and recovers Threads posts through Aside |
| [`alt-text-generator`](skills/alt-text-generator/) | Writes concise Korean alt text in plain text and HTML forms |
| [`threads-brand-card`](skills/threads-brand-card/) | Builds branded card images with reproducible HTML and CSS |
| [`threads-html-image`](skills/threads-html-image/) | Renders text, metrics, and screenshots to PNG |

### `threads-web-publish` references

| Document | Description |
|---|---|
| `composing.md` | Compose posts, replies, and media attachments |
| `scheduling.md` | Schedule posts and find scheduled drafts |
| `recovery.md` | Correct posts and recover from publishing mistakes |
| `dm-source.md` | Turn DM conversations into attributed post material |

## Rules in short

- Aim for 25 characters per line; 40 is the upper limit
- Keep paragraphs to 4 lines or fewer
- Break after commas that end a clause, not commas in lists or numbers
- Omit sentence-ending periods; preserve periods in URLs, numbers, versions, and filenames
- Use zero hashtags by default

## Checker

```bash
python3 skills/threads-linebreak/scripts/check_linebreaks.py draft.txt
```

Example output:

```
── 분포 ──
문단 2개 · 줄 3개 · 본문 50자(줄바꿈 제외)
줄 길이 평균 16.7자 · 40자 이하 100% (현재 기준)
문단 1~2줄 비율 100% (권장) · 구성 [2, 1]
줄 끝 쉼표 33% (절 경계인지 확인)
줄 끝 문자 {',': 1, '다': 1, '간': 1}

── 고칠 것 없음 ──
```

Add `--json` for machine-readable output. The checker uses Python 3.8+ standard library only and exits 1 for violations.

## Install

### Claude Code plugin

```text
/plugin marketplace add Tygb99/threads-writing-skills
/plugin install threads-writing-skills@threads-writing-skills
/reload-plugins
```

Restart instead of `/reload-plugins` when needed, then verify with `claude plugin list`. Skill calls use the namespace, for example `/threads-writing-skills:threads-linebreak`.

### Codex plugin

```bash
codex plugin marketplace add Tygb99/threads-writing-skills
codex plugin add threads-writing-skills@threads-writing-skills
codex plugin list
```

Remove with `codex plugin remove` and `codex plugin marketplace remove` (check each command's `--help` for the required argument). Codex reads `.claude-plugin/marketplace.json` as the marketplace catalog and `.codex-plugin/plugin.json` as the plugin manifest.

### Aside and manual checkout install

Aside has no plugin system. Clone the repository and run:

```bash
git clone https://github.com/Tygb99/threads-writing-skills.git
cd threads-writing-skills
./install.sh
```

The script symlinks each skill into Aside (`~/.aside/u/0/skills/user`), Claude Code (`~/.claude/skills`), and Codex (`~/.codex/skills`), so a checkout can be used directly while developing. Override the targets with `CLAUDE_SKILLS_DIR`, `CODEX_SKILLS_DIR`, and `ASIDE_SKILLS_DIR`. Remove them with `./install.sh --uninstall`. Start Claude Code, Codex, and Aside again before checking recognition.

Browser publishing assumes Aside is running and logged in to Threads.

## License

MIT.
