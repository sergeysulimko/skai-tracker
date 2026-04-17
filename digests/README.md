# Digests

One file per stream per day, named `YYYY-MM-DD-<slug>.md`.

Active slugs:

- `anthropic-tools` — Claude Code / Chat / API / community
- `anthropic-news` — Anthropic as a company (strategy, partnerships, safety)

## Format

Contents are Telegram-flavoured HTML (sent with `parse_mode=HTML`). Allowed tags:

- `<b>`, `<i>`, `<code>`
- `<a href="URL">text</a>`
- `<blockquote>` — one per news item
- `<blockquote expandable>` — for "Как применить" / "Контекст" sections

Every opened tag must be closed. `<` `>` `&` inside text must be escaped as `&lt;` `&gt;` `&amp;`.

## Trigger push convention

The remote Claude Code Routine trigger reads the last 3 files here for dedup, then commits two new files (`*-anthropic-tools.md` and `*-anthropic-news.md`) in one commit to `main`. The tracker-notify workflow picks up the changed files via `git diff HEAD^ HEAD` and sends them to Telegram.

This README is excluded from both the workflow `paths` filter and the `git diff` collect step.
