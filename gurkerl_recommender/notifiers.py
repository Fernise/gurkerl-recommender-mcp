from __future__ import annotations

import json
import os
from html import escape
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib import parse, request

from gurkerl_recommender.config import NotifierConfig
from gurkerl_recommender.scoring import Recommendation


class Notifier(Protocol):
    def send(self, recommendations: list[Recommendation]) -> None:
        """Send recommendations to the user."""


class ConsoleNotifier:
    def send(self, recommendations: list[Recommendation]) -> None:
        if not recommendations:
            print("No new recommendations above the notification threshold.")
            return

        print("Recommended Gurkerl deals:")
        for recommendation in recommendations:
            product = recommendation.product
            print(f"- {product.name} | score {recommendation.score:g} | EUR {product.price:g}")
            print(f"  reasons: {'; '.join(recommendation.reasons)}")
            if recommendation.cautions:
                print(f"  cautions: {'; '.join(recommendation.cautions)}")


class TelegramNotifier:
    def __init__(
        self,
        bot_token_env: str = "TELEGRAM_BOT_TOKEN",
        chat_id_env: str = "TELEGRAM_CHAT_ID",
    ) -> None:
        self.bot_token = os.environ.get(bot_token_env)
        self.chat_id = os.environ.get(chat_id_env)
        missing = [
            name
            for name, value in (
                (bot_token_env, self.bot_token),
                (chat_id_env, self.chat_id),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(
                "Missing Telegram environment variables: " + ", ".join(missing)
            )

    def send(self, recommendations: list[Recommendation]) -> None:
        if not recommendations:
            return
        self._send_message(_format_telegram_message(recommendations))

    def send_text(self, text: str) -> None:
        self._send_message(text)

    def _send_message(self, text: str) -> None:
        assert self.bot_token is not None
        assert self.chat_id is not None
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = parse.urlencode(
            {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": "true",
            }
        ).encode("utf-8")
        http_request = request.Request(url, data=data, method="POST")
        try:
            with request.urlopen(http_request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            try:
                detail = error.read().decode("utf-8", errors="replace")
            except Exception:
                detail = error.reason or error.msg
            raise RuntimeError(f"Telegram HTTP {error.code}: {detail}") from error
        except URLError as error:
            raise RuntimeError(f"Telegram network error: {error.reason}") from error
        if not payload.get("ok"):
            raise RuntimeError(f"Telegram send failed: {payload}")


def _format_telegram_message(recommendations: list[Recommendation]) -> str:
    lines = [
        "🛒 <b>Gurkerl alert</b>",
        f"✨ {len(recommendations)} new deal(s) worth checking",
    ]
    for index, recommendation in enumerate(recommendations, start=1):
        product = recommendation.product
        score_label = _score_label(recommendation.score)
        product_name = escape(product.name)
        if product.detail_url:
            product_name = (
                f'<a href="{escape(product.detail_url, quote=True)}">{product_name}</a>'
            )
        lines.append("")
        lines.append(
            f"{_score_emoji(recommendation.score)} <b>{index}. {product_name}</b>"
        )
        lines.append(
            f"🎯 <b>{score_label}</b> · score {recommendation.score:g}"
        )
        lines.append(f"💶 <b>EUR {product.price:g}</b> · {escape(product.size or 'unit')}")
        if product.discount_percent:
            lines.append(f"🏷️ Discount: <b>-{product.discount_percent:g}%</b>")
        if product.expires_in_days is not None:
            lines.append(f"⏳ Use soon: {product.expires_in_days} day(s)")
        lines.append(f"📊 Nutrition: {_nutrition_source_icon(product.nutrition_source)} {_nutrition_source_label(product.nutrition_source)}")
        lines.append("✅ " + escape(" · ".join(recommendation.reasons[:3])))
        cautions = _visible_cautions(recommendation)
        if cautions:
            lines.append("⚠️ " + escape(" · ".join(cautions[:2])))
    return "\n".join(lines)


def _score_label(score: float) -> str:
    if score >= 110:
        return "excellent"
    if score >= 90:
        return "strong"
    if score >= 70:
        return "good"
    return "maybe"


def _score_emoji(score: float) -> str:
    if score >= 110:
        return "🔥"
    if score >= 90:
        return "💪"
    if score >= 70:
        return "👍"
    return "🤔"


def _visible_cautions(recommendation: Recommendation) -> tuple[str, ...]:
    if recommendation.product.expires_in_days is None:
        return recommendation.cautions
    return tuple(
        caution
        for caution in recommendation.cautions
        if not caution.startswith("expires in ")
    )


def _nutrition_source_label(source: str) -> str:
    if source == "exact":
        return "exact macros"
    if source == "unavailable":
        return "unavailable"
    return "estimated macros"


def _nutrition_source_icon(source: str) -> str:
    if source == "exact":
        return "🧾"
    if source == "unavailable":
        return "❔"
    return "🧮"


def build_notifier(config: NotifierConfig) -> Notifier:
    if config.type == "console":
        return ConsoleNotifier()
    if config.type == "telegram":
        return TelegramNotifier(
            bot_token_env=config.bot_token_env,
            chat_id_env=config.chat_id_env,
        )
    raise ValueError(f"Unknown notifier: {config.type}")
