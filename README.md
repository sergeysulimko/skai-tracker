# SKAI Tracker

Minimal repository used as a shuttle between a remote Claude Code Routine trigger and a Telegram bot.

## Flow

```
claude.ai trigger (cron 04:00 UTC = 09:00 Asia/Yekaterinburg)
  ↓ research via WebSearch / WebFetch (Max Plan, $0)
  ↓ commits two HTML digests into digests/
  ↓ git push origin main
  ↓
GitHub Action .github/workflows/tracker-notify.yml
  ↓ on push paths: digests/**.md (README excluded)
  ↓ reads changed digest files
  ↓ POST https://api.telegram.org/bot{token}/sendMessage (parse_mode=HTML)
  → Telegram chat
```

## Why a separate repo

The main SKAI monorepo is ~19 GB (turbo cache) with full Next.js / pnpm / CI stack. Cloning it just to drop a markdown file is absurdly wasteful and the CI workflow would run on every digest merge. This repo has zero dependencies, no build, no lockfiles — clone is instant.

## Layout

```
skai-tracker/
├── .github/workflows/
│   ├── tracker-notify.yml   # main: on push → send digest to TG
│   └── tracker-alert.yml    # failure alert + 26h heartbeat (daily only)
├── notify.py                # plain python, stdlib only (handles daily + weekly markers)
├── digests/
│   ├── README.md            # convention, excluded from triggers
│   ├── YYYY-MM-DD-anthropic-{tools,news}.md  # generated daily by Daily trigger
│   └── YYYY-MM-DD-ai-weekly.md               # generated Saturdays by Weekly trigger
├── prompts/
│   ├── anthropic-daily.md   # daily trigger prompt (paste into claude.ai UI)
│   └── ai-weekly.md         # weekly trigger prompt (paste into claude.ai UI)
└── README.md
```

## Secrets required

GitHub repo secrets (`gh secret set`):

- `TELEGRAM_BOT_TOKEN`
- `TRACKER_TELEGRAM_CHAT_ID`

## Trigger setup

### Daily trigger (Anthropic tools + news)

1. `trig_016xQ1ZWXEdHNh1e1jGLCwNd` on https://claude.ai/settings/triggers.
2. Repository: `sergeysulimko/skai-tracker` with write-permissions (GitHub App connector).
3. Schedule: `0 4 * * *` (09:00 Asia/Yekaterinburg).
4. Network access: Trusted (only WebSearch/WebFetch needed; api.telegram.org is **not** called from the sandbox).
5. Prompt: contents of `prompts/anthropic-daily.md` — the block inside ``` ``` fences.

### Weekly trigger (AI industry digest, Saturday mornings)

Architecture: **main Sonnet orchestrator + 7 parallel Sonnet subagents** (Task tool), one per category (Models, Products, Open Source, Infra, Hardware, Regulation, People). Self-healing — retry failed subagents, fall back to direct WebSearch, skip empty sections gracefully.

1. Create new trigger on https://claude.ai/settings/triggers — name `SKAI Tracker — AI Weekly`.
2. Repository: `sergeysulimko/skai-tracker` with write-permissions (reuse the same GitHub App connector).
3. Schedule: `3 1 * * 6` (06:03 Asia/Yekaterinburg — Saturday).
4. Model: `claude-sonnet-4-6`.
5. Tools: Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, **Task** (needed for parallel subagents).
6. Network access: **Trusted** (WebSearch/WebFetch; api.telegram.org is **not** called from the sandbox).
7. Prompt: contents of `prompts/ai-weekly.md` — the block inside ``` ``` fences.

Weekly digest arrives every Saturday ~06:05 local (one push event per week; `notify.py` chunks it into 4–6 Telegram messages automatically).

**Why Sonnet + subagents, not Opus solo**: Main orchestrator and all 7 category researchers run on Sonnet 4.6 — WebSearch/verification/Russian synthesis don't require Opus reasoning. Parallel subagents cut wall-clock time ~3–4x (7 categories researched concurrently) and isolate context per category, so main agent synthesizes from 7 compressed reports instead of juggling everything.

## Manual digest push (testing)

```bash
git add digests/YYYY-MM-DD-anthropic-tools.md
git commit -m "test: manual digest"
git push origin main
gh run watch --repo sergeysulimko/skai-tracker
```

## Why plain text / HTML

Messages go to Telegram with `parse_mode=HTML`. Digest files already contain Telegram-flavoured HTML (`<b>`, `<blockquote>`, `<a href="">`, `<blockquote expandable>`). The sender preserves formatting and falls back to stripped text on HTTP 400.
