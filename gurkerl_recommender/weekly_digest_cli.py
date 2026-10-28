from __future__ import annotations

import argparse
from pathlib import Path

from gurkerl_recommender.config import AppConfig
from gurkerl_recommender.env import load_dotenv
from gurkerl_recommender.notifiers import TelegramNotifier
from gurkerl_recommender.weekly_digest import build_weekly_digest


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Send or print a weekly Gurkerl digest.")
    parser.add_argument("--config", type=Path, default=Path("config.telegram.json"))
    parser.add_argument(
        "--profile",
        type=Path,
        default=Path("profiles/july-budget-profile.json"),
    )
    parser.add_argument("--deal-limit", type=int, default=6)
    parser.add_argument("--send", action="store_true", help="Send digest to Telegram.")
    args = parser.parse_args()

    try:
        config = AppConfig.from_file(args.config)
        digest = build_weekly_digest(config, args.profile, args.deal_limit)
        if args.send:
            TelegramNotifier(
                bot_token_env=config.notifier.bot_token_env,
                chat_id_env=config.notifier.chat_id_env,
            ).send_text(digest)
        else:
            print(digest)
    except RuntimeError as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
