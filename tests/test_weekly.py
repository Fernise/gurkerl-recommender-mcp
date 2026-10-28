import unittest

from gurkerl_recommender.order_history import HistoryItem
from gurkerl_recommender.weekly import build_weekly_plan, canonical_name, categorize_product


class WeeklyTest(unittest.TestCase):
    def test_categorize_product(self) -> None:
        self.assertEqual(categorize_product("Eier aus Freilandhaltung M 10er"), "protein")
        self.assertEqual(categorize_product("Miil BIO Joghurt Natur"), "dairy")
        self.assertEqual(categorize_product("CeraVe Feuchtigkeitscreme"), "household")
        self.assertEqual(categorize_product("Berger Wellness Schinken geschnitten"), "processed_protein")

    def test_canonical_name_groups_eggs(self) -> None:
        self.assertEqual(
            canonical_name("Nest Ei Eier aus Freilandhaltung M 10er"),
            "Eier aus Freilandhaltung M 10er",
        )

    def test_build_weekly_plan_budget(self) -> None:
        items = [
            HistoryItem("Eier aus Freilandhaltung M 10er", "10 Stk", 3.99, "2026-05-01"),
            HistoryItem("Eier aus Freilandhaltung M 10er", "10 Stk", 3.99, "2026-05-08"),
            HistoryItem("Eier aus Freilandhaltung M 10er", "10 Stk", 3.99, "2026-05-15"),
            HistoryItem("CeraVe Feuchtigkeitscreme", "340 g", 14.9, "2026-05-01"),
        ]

        plan = build_weekly_plan(items, 200, 250, 9)

        self.assertEqual(plan.target_cycle_budget_min, 60)
        self.assertEqual(plan.target_cycle_budget_max, 75)
        self.assertEqual(plan.staples[0].name, "Eier aus Freilandhaltung M 10er")
        self.assertEqual(plan.limit_or_skip[0].name, "CeraVe Feuchtigkeitscreme")


if __name__ == "__main__":
    unittest.main()
