# threads-writing-skills

Agent skills for writing Threads posts in Korean. **The same files work in both Claude Code and Codex.**

The rules are measured, not guessed. They come from 4 months of official Threads API reports for [@yong_____jjang](https://www.threads.com/@yong_____jjang) (2026-04 to 2026-07) — **397 post captions and self-replies**, counted line by line.

![Same post, different line breaks](assets/before-after.png)

Both sides are 152 characters. Line breaks don't change length. They change reading speed.

한국어 문서: [README.ko.md](README.ko.md)

---

## Skills

| Skill | What it does |
|---|---|
| [`threads-linebreak`](threads-linebreak/) | Shapes line breaks and paragraphs to the measured pattern, and ships a checker that catches violations |
| [`threads-web-publish`](threads-web-publish/) | The operational procedure for driving Threads on the web with browser automation. `SKILL.md` holds the four hard rules and the pre-publish checklist; situational detail lives in four `references/` documents |
| [`alt-text-generator`](alt-text-generator/) | Writes Korean alt text for an image — front-loads the key information, transcribes text inside the image, and returns both plain text and an `alt="…"` attribute |

### `threads-web-publish` reference documents

`SKILL.md` carries only the four rules you apply every time plus the pre-publish checklist. Open the one document that matches the task at hand.

| Document | Covers |
|---|---|
| `references/composing.md` | Body and self-reply input, photo attachment, alt text, caret and scroll traps |
| `references/scheduling.md` | Scheduling, finding a scheduled post again, quote cards, why the API cannot schedule |
| `references/recovery.md` | Fixing a published post, pinning replies, clicks you cannot undo |
| `references/dm-source.md` | Turning a DM thread into post material (attributing speakers and input paths) |

---

## The rules in short

> **One line break after a comma that ends a clause.**
> **Two line breaks (one blank line) between paragraphs.**

- Not every comma — only **44%** of commas land at end of line. The rest are numbers and lists; leave them inline
- Average line is **25 characters**; **86% are 40 or fewer**
- **76% of paragraphs are 1–2 lines.** Past 3 lines, look for a place to split
- **Half of all lines end with a period.** Comma breaks are seasoning, not the base

Full reasoning and examples live in [`threads-linebreak/SKILL.md`](threads-linebreak/SKILL.md) (written in Korean, since that's the language the pattern describes).

---

## The checker

```bash
python3 threads-linebreak/scripts/check_linebreaks.py draft.txt
```

No dependencies (Python 3.8+). It separates hard violations from judgment calls — whether a comma joins clauses or items in a list depends on context, so the script flags candidates and leaves the decision to a human.

```
── 분포 ──
문단 5개 · 줄 8개 · 본문 153자(줄바꿈 제외)
줄 길이 평균 19.1자 · 40자 이하 100% (실측 기준 86%)
문단 1~2줄 비율 100% (실측 기준 76%) · 구성 [2, 2, 2, 1, 1]

── 고칠 것 없음 ──
```

Add `--json` for machine-readable output. Exits 1 when violations exist, so it drops into CI or a pre-publish hook.

---

## Install

```bash
git clone https://github.com/Tygb99/threads-writing-skills.git
cd threads-writing-skills
./install.sh
```

`install.sh` only creates links — it never copies or deletes:

- **Claude Code** → symlinks at `~/.claude/skills/<skill-name>`
- **Codex** → pointer lines appended to `~/.codex/AGENTS.md`

After that, a single `git pull` updates both.

To do it by hand, link or copy the skill folder wherever your tool reads skills from. Both tools use the same `SKILL.md` format (YAML frontmatter + markdown).

---

## License

MIT. If you use this, consider re-deriving the numbers from your own account — these come from one person's 397 posts, and a different voice will produce a different distribution.
