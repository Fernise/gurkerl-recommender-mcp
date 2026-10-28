import unittest

from gurkerl_recommender.models import Nutrition, Product, UserProfile
from gurkerl_recommender.sample_data import SAMPLE_PRODUCTS
from gurkerl_recommender.scoring import recommend_products


class ScoringTest(unittest.TestCase):
    def test_save_food_high_protein_meat_ranks_first(self) -> None:
        recommendations = recommend_products(SAMPLE_PRODUCTS, UserProfile())

        self.assertEqual(recommendations[0].product.id, "save-food-turkey-mince")
        self.assertTrue(any("Save Food" in reason for reason in recommendations[0].reasons))
        self.assertTrue(recommendations[0].cautions)

    def test_never_buy_keywords_block_product(self) -> None:
        recommendations = recommend_products(SAMPLE_PRODUCTS, UserProfile())

        self.assertNotIn("sugary-drink", {item.product.id for item in recommendations})

    def test_high_sugar_product_gets_penalized(self) -> None:
        product = Product(
            id="sweet-yogurt",
            name="Sweet yogurt",
            category="dairy",
            price=1.2,
            nutrition_per_100g=Nutrition(protein_g=4, sugar_g=14, calories=120),
        )

        recommendation = recommend_products([product], UserProfile())[0]

        self.assertLess(recommendation.score, 20)
        self.assertTrue(
            any("sugar is high" in caution for caution in recommendation.cautions)
        )

    def test_price_per_protein_bonus_requires_meaningful_protein(self) -> None:
        product = Product(
            id="cheap-vegetable",
            name="Cheap vegetable",
            category="vegetables",
            price=0.2,
            nutrition_per_100g=Nutrition(protein_g=2, sugar_g=3, calories=40),
        )

        recommendation = recommend_products([product], UserProfile())[0]

        self.assertFalse(
            any("strong price per protein" in reason for reason in recommendation.reasons)
        )


if __name__ == "__main__":
    unittest.main()
