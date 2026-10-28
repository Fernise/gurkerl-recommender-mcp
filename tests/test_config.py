import unittest

from gurkerl_recommender.config import AppConfig


class ConfigTest(unittest.TestCase):
    def test_source_detail_enrichment_config(self) -> None:
        config = AppConfig.from_dict(
            {
                "source": {
                    "type": "gurkerl_public",
                    "enrich_details": True,
                    "enrich_limit": 5,
                }
            }
        )

        self.assertTrue(config.source.enrich_details)
        self.assertEqual(config.source.enrich_limit, 5)


if __name__ == "__main__":
    unittest.main()
