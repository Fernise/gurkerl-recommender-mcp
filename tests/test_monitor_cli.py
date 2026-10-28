import unittest
from unittest.mock import patch

from gurkerl_recommender import monitor_cli


class MonitorCliTest(unittest.TestCase):
    def test_runtime_error_exits_cleanly(self) -> None:
        with patch(
            "sys.argv",
            ["monitor_cli", "--config", "config.example.json"],
        ), patch(
            "gurkerl_recommender.monitor_cli.AppConfig.from_file",
            side_effect=RuntimeError("clean error"),
        ):
            with self.assertRaisesRegex(SystemExit, "clean error"):
                monitor_cli.main()


if __name__ == "__main__":
    unittest.main()
