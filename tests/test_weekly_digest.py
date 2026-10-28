import unittest

from gurkerl_recommender.models import Product
from gurkerl_recommender.scoring import Recommendation
from gurkerl_recommender.weekly_digest import JulyBudgetProfile, format_weekly_digest


class WeeklyDigestTest(unittest.TestCase):
    def test_format_weekly_digest(self) -> None:
        profile = JulyBudgetProfile(
            monthly_budget_min=200,
            monthly_budget_max=250,
            cycle_days=9,
            cycle_budget_min=60,
            cycle_budget_max=75,
            staples=("Eggs", "Rice"),
            flexible_targets=("Tuna",),
            limit=("snacks",),
        )
        digest = format_weekly_digest(
            profile,
            [
                Recommendation(
                    product=Product(
                        id="1",
                        name="Tuna",
                        category="protein",
                        price=2.5,
                        detail_url="https://www.gurkerl.at/tuna",
                        nutrition_source="exact",
                    ),
                    score=95,
                    reasons=("high protein",),
                    cautions=(),
                )
            ],
        )

        self.assertIn("EUR 60-75", digest)
        self.assertIn("Eggs", digest)
        self.assertIn("Tuna", digest)
        self.assertIn("exact", digest)
        self.assertIn("🧺", digest)
        self.assertIn("🔥", digest)


if __name__ == "__main__":
    unittest.main()
