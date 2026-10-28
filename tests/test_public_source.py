import json
import unittest
from unittest.mock import patch

from gurkerl_recommender.models import Product
from gurkerl_recommender.sources import (
    enrich_gurkerl_public_detail,
    parse_gurkerl_detail_nutrition_html,
    parse_gurkerl_public_html,
    parse_gurkerl_public_lines,
)


class PublicSourceTest(unittest.TestCase):
    def test_parse_detail_nutrition(self) -> None:
        payload = {
            "props": {
                "initialProps": {
                    "pageProps": {
                        "dehydratedState": {
                            "queries": [
                                {
                                    "state": {
                                        "data": {
                                            "composition": {
                                                "nutritionalValues": [
                                                    {
                                                        "portion": "100 g",
                                                        "values": {
                                                            "energyKCal": {
                                                                "amount": 75,
                                                                "unit": "kCal",
                                                            },
                                                            "fats": {
                                                                "amount": 0.2,
                                                                "unit": "g",
                                                            },
                                                            "carbohydrates": {
                                                                "amount": 9.1,
                                                                "unit": "g",
                                                            },
                                                            "sugars": {
                                                                "amount": 8.5,
                                                                "unit": "g",
                                                            },
                                                            "protein": {
                                                                "amount": 8.5,
                                                                "unit": "g",
                                                            },
                                                        },
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }
        html = (
            '<script id="__NEXT_DATA__" type="application/json">'
            + json.dumps(payload)
            + "</script>"
        )

        nutrition = parse_gurkerl_detail_nutrition_html(html)

        self.assertIsNotNone(nutrition)
        assert nutrition is not None
        self.assertEqual(nutrition.calories, 75)
        self.assertEqual(nutrition.protein_g, 8.5)
        self.assertEqual(nutrition.sugar_g, 8.5)

    def test_enrich_product_with_exact_nutrition(self) -> None:
        payload = {
            "props": {
                "initialProps": {
                    "pageProps": {
                        "dehydratedState": {
                            "queries": [
                                {
                                    "state": {
                                        "data": {
                                            "composition": {
                                                "nutritionalValues": [
                                                    {
                                                        "values": {
                                                            "energyKCal": {"amount": 90},
                                                            "sugars": {"amount": 1},
                                                            "protein": {"amount": 20},
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }
        html = (
            '<script id="__NEXT_DATA__" type="application/json">'
            + json.dumps(payload)
            + "</script>"
        )
        product = Product(
            id="1",
            name="Protein test",
            category="meat",
            price=3,
            detail_url="https://www.gurkerl.at/product",
        )

        with patch("gurkerl_recommender.sources._fetch_text", return_value=html):
            enriched = enrich_gurkerl_public_detail(product)

        self.assertEqual(enriched.nutrition_source, "exact")
        self.assertEqual(enriched.nutrition_per_100g.protein_g, 20)

    def test_parse_next_data_products(self) -> None:
        payload = {
            "props": {
                "initialProps": {
                    "pageProps": {
                        "dehydratedState": {
                            "queries": [
                                {
                                    "state": {
                                        "data": {
                                            "pages": [
                                                {
                                                    "cardsData": [
                                                        {
                                                            "productId": 123,
                                                            "name": "Steirerhuhn AMA Flügerl gewürzt",
                                                            "slug": "steirerhuhn-ama-fluegerl-gewuerzt",
                                                            "brand": None,
                                                            "textualAmount": "ca. 0,53 kg",
                                                            "prices": {
                                                                "originalPrice": 5.75,
                                                                "salePrice": 2.04,
                                                                "saleText": "-64 %",
                                                            },
                                                            "stock": {
                                                                "availabilityStatus": "AVAILABLE"
                                                            },
                                                            "badges": [
                                                                {
                                                                    "type": "EXPIRING",
                                                                    "text": "Morgen verbrauchen",
                                                                }
                                                            ],
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }
        html = (
            '<script id="__NEXT_DATA__" type="application/json">'
            + json.dumps(payload)
            + "</script>"
        )

        products = parse_gurkerl_public_html(
            html,
            source_url="https://www.gurkerl.at/rette-lebensmittel",
        )

        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, "gurkerl-123")
        self.assertEqual(products[0].category, "meat")
        self.assertEqual(products[0].price, 2.04)
        self.assertEqual(products[0].discount_percent, 64)
        self.assertEqual(products[0].expires_in_days, 1)
        self.assertEqual(products[0].nutrition_source, "estimated")
        self.assertEqual(
            products[0].detail_url,
            "https://www.gurkerl.at/123-steirerhuhn-ama-fluegerl-gewuerzt",
        )

    def test_parse_save_food_products(self) -> None:
        lines = [
            "Fleisch & Fisch",
            "Morgen verbrauchen",
            "0 Stück im Korb",
            "ca. 2 04 € 5,75 € -64 % Steirerhuhn AMA Flügerl gewürzt",
            "ca. 0,53 kg",
            "3.83 €/kg",
            "Kühlregal",
            "Haltbar bis 16. 6.",
            "0 Stück im Korb",
            "1 35 € 1,59 € -15 % Schwarzwaldmilch Protein Topfen Creme Himbeere-Granatapfel",
            "200 g",
            "6.75 €/kg",
        ]

        products = parse_gurkerl_public_lines(
            lines,
            source_url="https://www.gurkerl.at/rette-lebensmittel",
        )

        self.assertEqual(len(products), 2)
        self.assertEqual(products[0].category, "meat")
        self.assertTrue(products[0].is_save_food)
        self.assertEqual(products[0].expires_in_days, 1)
        self.assertEqual(products[0].discount_percent, 64)
        self.assertEqual(products[1].category, "dairy")
        self.assertEqual(products[1].nutrition_per_100g.protein_g, 10)

    def test_infer_meat_and_egg_products_from_next_data(self) -> None:
        lines = [
            "0 Stück im Korb",
            "1 99 € 3,99 € -50 % Esterhazy Reh Keulensteak mariniert",
            "200 g",
            "0 Stück im Korb",
            "4 84 € 9,99 € -51 % Eifix BIO Vollei",
            "1 kg",
        ]

        products = parse_gurkerl_public_lines(
            lines,
            source_url="https://www.gurkerl.at/rette-lebensmittel",
        )

        categories = {product.name: product.category for product in products}
        self.assertEqual(categories["Esterhazy Reh Keulensteak mariniert"], "meat")
        self.assertEqual(categories["Eifix BIO Vollei"], "eggs")

    def test_parse_promotion_product(self) -> None:
        lines = [
            "Obst & Gemüse",
            "0 Stück im Korb",
            "2 39 € 2,99 € -20 % bis 16. 6. BIO Plum-Cherrytomaten",
            "250 g",
            "9.56 €/kg",
        ]

        products = parse_gurkerl_public_lines(
            lines,
            source_url="https://www.gurkerl.at/aktionen",
        )

        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].name, "BIO Plum-Cherrytomaten")
        self.assertTrue(products[0].is_promotion)
        self.assertFalse(products[0].is_save_food)


if __name__ == "__main__":
    unittest.main()
