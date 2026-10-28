from __future__ import annotations

import argparse
import json
import os
from urllib import parse as urllib_parse
from urllib import request
from urllib.error import HTTPError, URLError

from gurkerl_recommender.env import load_dotenv


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Telegram helper commands.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("get-updates")
    send_test = subparsers.add_parser("send-test")
    send_test.add_argument(
        "--message",
        default="Gurkerl recommender test message. Telegram is wired correctly.",
    )
    args = parser.parse_args()

    if args.command == "get-updates":
        _print_updates()
    elif args.command == "send-test":
        _send_test(args.message)


def _print_updates() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN")

    payload = _telegram_get(token, "getUpdates")
    results = payload.get("result", [])
    if not results:
        print("No updates found. Send /start to your bot in Telegram, then run again.")
        return

    seen: set[int] = set()
    for update in results:
        message = update.get("message") or update.get("edited_message")
        if not message:
            continue
        chat = message.get("chat", {})
        chat_id = chat.get("id")
        if chat_id in seen:
            continue
        seen.add(chat_id)
        title = chat.get("title") or chat.get("username") or chat.get("first_name") or ""
        print(f"TELEGRAM_CHAT_ID={chat_id} {title}".strip())

    if not seen:
        print("No message chats found. Send /start to your bot, then run again.")


def _send_test(message: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN")
    if not chat_id:
        raise SystemExit("Missing TELEGRAM_CHAT_ID")

    payload = _telegram_post(
        token,
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": "true",
        },
    )
    if payload.get("ok"):
        print("Telegram test message sent.")


def _telegram_get(token: str, method: str) -> dict[str, object]:
    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        with request.urlopen(url, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Telegram HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise SystemExit(f"Telegram network error: {error.reason}") from error
    if not payload.get("ok"):
        raise SystemExit(f"Telegram API error: {payload}")
    return payload


def _telegram_post(
    token: str,
    method: str,
    data: dict[str, str],
) -> dict[str, object]:
    url = f"https://api.telegram.org/bot{token}/{method}"
    encoded = urllib_parse.urlencode(data).encode("utf-8")
    try:
        with request.urlopen(url, data=encoded, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Telegram HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise SystemExit(f"Telegram network error: {error.reason}") from error
    if not payload.get("ok"):
        raise SystemExit(f"Telegram API error: {payload}")
    return payload


if __name__ == "__main__":
    main()
