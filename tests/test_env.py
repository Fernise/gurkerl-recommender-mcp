import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gurkerl_recommender.env import load_dotenv


class EnvTest(unittest.TestCase):
    def test_load_dotenv_sets_missing_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("A=one\nB='two'\n", encoding="utf-8")

            with patch.dict(os.environ, {"A": "existing"}, clear=True):
                load_dotenv(path)

                self.assertEqual(os.environ["A"], "existing")
                self.assertEqual(os.environ["B"], "two")


if __name__ == "__main__":
    unittest.main()
