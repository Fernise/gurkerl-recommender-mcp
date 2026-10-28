from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SourceConfig:
    type: str = "sample"
    products_path: Path | None = None
    urls: tuple[str, ...] = ()
    enrich_details: bool = False
    enrich_limit: int = 12


@dataclass(frozen=True)
class NotifierConfig:
    type: str = "console"
    bot_token_env: str = "TELEGRAM_BOT_TOKEN"
    chat_id_env: str = "TELEGRAM_CHAT_ID"


@dataclass(frozen=True)
class AppConfig:
    profile_path: Path = Path("profile.example.json")
    database_path: Path = Path("data/gurkerl_recommender.sqlite3")
    recommendation_limit: int = 10
    notification_threshold: float = 80
    notify_only_new_products: bool = True
    source: SourceConfig = SourceConfig()
    notifier: NotifierConfig = NotifierConfig()

    @classmethod
    def from_file(cls, path: Path) -> "AppConfig":
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        return cls.from_dict(payload, base_dir=path.parent)

    @classmethod
    def from_dict(cls, payload: dict[str, Any], base_dir: Path = Path(".")) -> "AppConfig":
        source = payload.get("source", {})
        notifier = payload.get("notifier", {})
        return cls(
            profile_path=_resolve_path(payload.get("profile_path"), base_dir)
            or cls.profile_path,
            database_path=_resolve_path(payload.get("database_path"), base_dir)
            or cls.database_path,
            recommendation_limit=int(payload.get("recommendation_limit", 10)),
            notification_threshold=float(payload.get("notification_threshold", 80)),
            notify_only_new_products=bool(payload.get("notify_only_new_products", True)),
            source=SourceConfig(
                type=str(source.get("type", "sample")),
                products_path=_resolve_path(source.get("products_path"), base_dir),
                urls=tuple(source.get("urls", ())),
                enrich_details=bool(source.get("enrich_details", False)),
                enrich_limit=int(source.get("enrich_limit", 12)),
            ),
            notifier=NotifierConfig(
                type=str(notifier.get("type", "console")),
                bot_token_env=str(
                    notifier.get("bot_token_env", "TELEGRAM_BOT_TOKEN")
                ),
                chat_id_env=str(notifier.get("chat_id_env", "TELEGRAM_CHAT_ID")),
            ),
        )


def _resolve_path(value: str | None, base_dir: Path) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return base_dir / path
