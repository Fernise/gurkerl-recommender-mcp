import unittest
from urllib.error import HTTPError
from unittest.mock import patch

from gurkerl_recommender.models import Product
from gurkerl_recommender.notifiers import TelegramNotifier
from gurkerl_recommender.scoring import Recommendation


class TelegramNotifierErrorTest(unittest.TestCase):
    def test_http_error_is_clean_runtime_error(self) -> None:
        error = HTTPError(
            url="https://api.telegram.org",
            code=403,
            msg="Forbidden",
            hdrs={},
            fp=None,
        )

        with patch.dict(
            "os.environ",
            {"TELEGRAM_BOT_TOKEN": "token", "TELEGRAM_CHAT_ID": "123"},
            clear=True,
        ), patch(
            "gurkerl_recommender.notifiers.request.urlopen",
            side_effect=error,
        ):
            notifier = TelegramNotifier()
            with self.assertRaisesRegex(RuntimeError, "Telegram HTTP 403"):
                notifier.send(
                    [
                        Recommendation(
                            product=Product(
                                id="1",
                                name="Turkey",
                                category="meat",
                                price=3,
                            ),
                            score=90,
                            reasons=("high protein",),
                            cautions=(),
                        )
                    ]
                )


if __name__ == "__main__":
    unittest.main()
