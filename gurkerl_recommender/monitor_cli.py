from __future__ import annotations

import argparse
from pathlib import Path

from gurkerl_recommender.config import AppConfig
from gurkerl_recommender.env import load_dotenv
from gurkerl_recommender.monitor import run_once


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Run the Gurkerl recommender monitor.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.example.json"),
        help="Path to monitor config JSON.",
    )
    args = parser.parse_args()

    try:
        config = AppConfig.from_file(args.config)
        run_once(config)
    except RuntimeError as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
