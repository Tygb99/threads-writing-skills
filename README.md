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

### Jev judgment (`--jev`, experimental)

Added in 1.1.0. Pass `--jev` to either checker (`check_linebreaks.py`, `check_first_paragraph.py`) to ask Jev first for the judgments that were left to a human. Jev is TypeSafe's System One model, called through Vercel AI Gateway (`typesafe-ai/jev`).

```bash
AI_GATEWAY_API_KEY=... python3 skills/threads-linebreak/scripts/check_linebreaks.py draft.txt --jev
AI_GATEWAY_API_KEY=... python3 skills/threads-linebreak/scripts/check_first_paragraph.py draft.txt --jev
```

- The line-break checker classifies each comma as a clause boundary or a list comma and shows only the ones that disagree with the actual line position, ordered by confidence
- The first-paragraph checker adds the subject type (event, artifact, other) and the probability that the first line is left open
- The `AI_GATEWAY_API_KEY` environment variable is required; without it the checker exits 2. When the call fails, the checker falls back to rule-based judgment and writes the reason to stderr
- Without `--jev` nothing leaves your machine, as before. With `--jev` the paragraph under check is sent to Vercel AI Gateway
- Measured on 2026-09-22: 89.1% accuracy against 46 human labels, 96.8% when limited to confidence 0.7 or higher. The sample is small, so treat it as a reference value
- Jev only decides what to look at first. The final call stays with a human

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

### Aside, omo, and manual checkout install

Aside has no plugin system. Agents that read the shared skills folder, such as omo, install the same way. Clone the repository and run:

```bash
git clone https://github.com/Tygb99/threads-writing-skills.git
cd threads-writing-skills
./install.sh
```

The script symlinks each skill into four places, so a checkout can be used directly while developing.

| Target | Path | Override with |
|---|---|---|
| Aside | `~/.aside/u/0/skills/user` | `ASIDE_SKILLS_DIR` |
| Claude Code | `~/.claude/skills` | `CLAUDE_SKILLS_DIR` |
| Codex | `~/.codex/skills` | `CODEX_SKILLS_DIR` |
| Shared folder | `~/.agents/skills` | `AGENTS_SKILLS_DIR` |

The shared folder `~/.agents/skills` is the Agent Skills standard location. omo, Codex, Cursor, OpenCode, and Pi read it (checked on 2026-09-27 against each project's official docs and by running omo and Codex). Claude Code and Aside read only their own folders, so they are linked separately. Codex 0.157.0 lists a skill once even when it exists in both `~/.codex/skills` and `~/.agents/skills`.

Remove the links with `./install.sh --uninstall`. Start the agents again before checking recognition.

Browser publishing assumes Aside is running and logged in to Threads.

## Changelog

- 1.1.0 (2026-09-27)
  - Added the experimental Jev judgment option `--jev` to the `threads-linebreak` checkers
  - `install.sh` now also links into the shared skills folder `~/.agents/skills`
  - Added completion criteria and external-text handling lines to the `threads-web-publish` delegation and routine prompts
- 1.0.0 (2026-09-22): first release in plugin format

## License

MIT.
