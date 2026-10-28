import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from gurkerl_recommender.config import AppConfig
from gurkerl_recommender.monitor import run_once
from gurkerl_recommender.storage import RecommendationStore


class MonitorTest(unittest.TestCase):
    def test_monitor_notifies_only_new_products_when_configured(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = AppConfig(
                profile_path=Path("profile.example.json"),
                database_path=root / "recommendations.sqlite3",
                notification_threshold=80,
                notify_only_new_products=True,
            )

            with redirect_stdout(StringIO()):
                first_run = run_once(config)
                second_run = run_once(config)

            self.assertTrue(first_run)
            self.assertEqual(second_run, [])

    def test_failed_notifier_does_not_mark_products_as_notified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database_path = root / "recommendations.sqlite3"
            config = AppConfig(
                profile_path=Path("profile.example.json"),
                database_path=database_path,
                notification_threshold=80,
                notify_only_new_products=True,
            )

            with patch(
                "gurkerl_recommender.notifiers.ConsoleNotifier.send",
                side_effect=RuntimeError("send failed"),
            ):
                with self.assertRaisesRegex(RuntimeError, "send failed"):
                    run_once(config)

            with RecommendationStore(database_path) as store:
                self.assertFalse(store.has_notified("save-food-turkey-mince"))


if __name__ == "__main__":
    unittest.main()
