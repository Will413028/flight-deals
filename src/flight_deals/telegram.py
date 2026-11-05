"""Send a Telegram message through the Bot API."""

from __future__ import annotations

import httpx


def send(token: str, chat_id: str, text: str) -> None:
    r = httpx.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"},
        timeout=20,
    )
    if r.status_code != 200:
        # never include the URL: it carries the bot token
        raise RuntimeError(f"telegram send failed: HTTP {r.status_code}")
