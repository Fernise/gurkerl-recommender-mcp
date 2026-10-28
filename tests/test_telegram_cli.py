import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from gurkerl_recommender.telegram_cli import _print_updates, _send_test


class TelegramCliTest(unittest.TestCase):
    def test_print_updates_shows_chat_id(self) -> None:
        payload = {
            "ok": True,
            "result": [
                {
                    "message": {
                        "chat": {
                            "id": 123,
                            "first_name": "Fer",
                        }
                    }
                }
            ],
        }

        with patch.dict(
            "os.environ",
            {"TELEGRAM_BOT_TOKEN": "token"},
            clear=True,
        ), patch(
            "gurkerl_recommender.telegram_cli._telegram_get",
            return_value=payload,
        ), redirect_stdout(io.StringIO()) as output:
            _print_updates()

        self.assertIn("TELEGRAM_CHAT_ID=123", output.getvalue())

    def test_send_test_uses_configured_chat(self) -> None:
        with patch.dict(
            "os.environ",
            {"TELEGRAM_BOT_TOKEN": "token", "TELEGRAM_CHAT_ID": "123"},
            clear=True,
        ), patch(
            "gurkerl_recommender.telegram_cli._telegram_post",
            return_value={"ok": True},
        ) as telegram_post, redirect_stdout(io.StringIO()) as output:
            _send_test("hello")

        telegram_post.assert_called_once()
        self.assertIn("Telegram test message sent.", output.getvalue())


if __name__ == "__main__":
    unittest.main()
