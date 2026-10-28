import os
import unittest
from unittest.mock import patch

from gurkerl_recommender.config import NotifierConfig
from gurkerl_recommender.models import Nutrition, Product
from gurkerl_recommender.notifiers import (
    TelegramNotifier,
    _format_telegram_message,
    build_notifier,
)
from gurkerl_recommender.scoring import Recommendation


class NotifierTest(unittest.TestCase):
    def test_telegram_notifier_requires_env(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "TELEGRAM_BOT_TOKEN"):
                TelegramNotifier()

    def test_build_telegram_notifier(self) -> None:
        with patch.dict(
            os.environ,
            {"TELEGRAM_BOT_TOKEN": "token", "TELEGRAM_CHAT_ID": "123"},
            clear=True,
        ):
            notifier = build_notifier(NotifierConfig(type="telegram"))

        self.assertIsInstance(notifier, TelegramNotifier)

    def test_format_message_contains_reasons_and_cautions(self) -> None:
        recommendation = Recommendation(
            product=Product(
                id="1",
                name="Turkey mince",
                category="meat",
                price=3.49,
                size="400g",
                nutrition_per_100g=Nutrition(protein_g=22, sugar_g=0),
                detail_url="https://www.gurkerl.at/example",
                discount_percent=35,
            ),
            score=95,
            reasons=("high protein", "Save Food deal"),
            cautions=("expires tomorrow",),
        )

        message = _format_telegram_message([recommendation])

        self.assertIn("Turkey mince", message)
        self.assertIn("high protein", message)
        self.assertIn("expires tomorrow", message)
        self.assertIn("💪", message)
        self.assertIn('<a href="https://www.gurkerl.at/example">Turkey mince</a>', message)
        self.assertIn("🛒", message)
        self.assertIn("Nutrition: 🧮 estimated macros", message)


if __name__ == "__main__":
    unittest.main()
