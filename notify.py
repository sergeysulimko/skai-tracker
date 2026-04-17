#!/usr/bin/env python3
"""Send tracker digest HTML files to Telegram.

Invoked by .github/workflows/tracker-notify.yml after a remote Claude Code
Routine trigger commits new files under digests/.

Files contain Telegram-flavoured HTML (<b>, <blockquote>, <a href="">, etc.).
Sent with parse_mode=HTML and disable_web_page_preview=True.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request

MAX_LEN = 4000
API_URL = "https://api.telegram.org/bot{token}/sendMessage"
MAX_ATTEMPTS = 4
BACKOFF_BASE = 2.0
BETWEEN_CHUNK_SLEEP = 0.5


def _post(url: str, payload: bytes) -> tuple[int, str]:
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return resp.status, body


def send_message(
    token: str,
    chat_id: str,
    text: str,
    parse_mode: str = "HTML",
) -> None:
    payload_dict = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if parse_mode:
        payload_dict["parse_mode"] = parse_mode
    payload = json.dumps(payload_dict).encode("utf-8")
    url = API_URL.format(token=token)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            status, body = _post(url, payload)
            print(f"TG {status} {body[:200]}")
            return
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            retry_after = 0
            if exc.code == 429:
                try:
                    parsed = json.loads(body)
                    retry_after = int(
                        parsed.get("parameters", {}).get("retry_after", 0)
                    )
                except Exception:
                    retry_after = 0
            print(
                f"TG HTTP {exc.code} attempt {attempt}/{MAX_ATTEMPTS}: {body[:300]}",
                file=sys.stderr,
            )
            if exc.code == 400 and attempt == 1 and parse_mode == "HTML":
                print("Retrying without parse_mode (strip HTML)...", file=sys.stderr)
                send_message(token, chat_id, _strip_html(text), parse_mode="")
                return
            if exc.code < 500 and exc.code != 429:
                raise SystemExit(1)
            if attempt == MAX_ATTEMPTS:
                raise SystemExit(1)
            delay = retry_after or (BACKOFF_BASE**attempt)
            time.sleep(delay)
        except urllib.error.URLError as exc:
            print(
                f"TG network error attempt {attempt}/{MAX_ATTEMPTS}: {exc}",
                file=sys.stderr,
            )
            if attempt == MAX_ATTEMPTS:
                raise SystemExit(1)
            time.sleep(BACKOFF_BASE**attempt)


_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    out = _TAG_RE.sub("", text)
    for entity, char in [("&lt;", "<"), ("&gt;", ">"), ("&amp;", "&")]:
        out = out.replace(entity, char)
    return out


_SELF_CLOSING_TAGS = frozenset({"br", "hr", "img"})
_BLOCK_BOUNDARY_RE = re.compile(
    r"\n(?=<(?:blockquote|b>(?:📰|🔧|📊|💡|🗞️|🔥|🧠|📦|🔓|🖥|⚖️|👔|👀)))",
    re.IGNORECASE,
)


def _close_open_tags(text: str) -> str:
    stack: list[str] = []
    for m in re.finditer(r"<(/?)(\w+)[\s>]", text):
        is_close = m.group(1) == "/"
        tag = m.group(2).lower()
        if tag in _SELF_CLOSING_TAGS:
            continue
        if is_close:
            if stack and stack[-1] == tag:
                stack.pop()
        else:
            stack.append(tag)
    return text + "".join(f"</{t}>" for t in reversed(stack))


def html_chunks(text: str, size: int = MAX_LEN) -> list[str]:
    if len(text) <= size:
        return [text]
    parts = _BLOCK_BOUNDARY_RE.split(text)
    result: list[str] = []
    buf = ""
    for part in parts:
        if len(buf) + len(part) <= size:
            buf += part
        else:
            if buf:
                result.append(_close_open_tags(buf.rstrip()))
            if len(part) <= size:
                buf = part
            else:
                for i in range(0, len(part), size):
                    sub = part[i : i + size]
                    if i + size < len(part):
                        result.append(_close_open_tags(sub))
                    else:
                        buf = sub
    if buf:
        result.append(_close_open_tags(buf.rstrip()))
    return result


def main() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TRACKER_TELEGRAM_CHAT_ID"]
    raw = os.environ.get("DIGEST_FILES", "")
    files = [
        line.strip()
        for line in raw.replace(" ", "\n").splitlines()
        if line.strip()
    ]

    if not files:
        print("No digest files provided; nothing to send.")
        return

    for rel in files:
        path = pathlib.Path(rel)
        if not path.is_file():
            print(f"Skip missing file: {rel}")
            continue
        body = path.read_text(encoding="utf-8").strip()
        if not body:
            print(f"Skip empty file: {rel}")
            continue
        pieces = html_chunks(body, MAX_LEN)
        for idx, chunk in enumerate(pieces):
            send_message(token, chat_id, chunk)
            if idx != len(pieces) - 1:
                time.sleep(BETWEEN_CHUNK_SLEEP)
        print(f"Sent: {rel}")


if __name__ == "__main__":
    main()
