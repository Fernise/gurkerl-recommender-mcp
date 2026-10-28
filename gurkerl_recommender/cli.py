from __future__ import annotations

import argparse
import json
from pathlib import Path

from gurkerl_recommender.models import Product, UserProfile
from gurkerl_recommender.sample_data import SAMPLE_PRODUCTS
from gurkerl_recommender.scoring import recommend_products


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank Gurkerl product candidates.")
    parser.add_argument("--sample", action="store_true", help="Use bundled sample data.")
    parser.add_argument("--products", type=Path, help="JSON file containing products.")
    parser.add_argument("--profile", type=Path, help="JSON file containing profile settings.")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    profile = _load_profile(args.profile)
    products = SAMPLE_PRODUCTS if args.sample else _load_products(args.products)
    recommendations = recommend_products(products, profile, limit=args.limit)

    for index, recommendation in enumerate(recommendations, start=1):
        product = recommendation.product
        print(f"{index}. {product.name} - score {recommendation.score:g}")
        print(f"   price: EUR {product.price:g} / {product.size or 'unit'}")
        print(f"   reasons: {'; '.join(recommendation.reasons) or 'no strong match'}")
        if recommendation.cautions:
            print(f"   cautions: {'; '.join(recommendation.cautions)}")


def _load_profile(path: Path | None) -> UserProfile:
    if path is None:
        return UserProfile()
    with path.open("r", encoding="utf-8") as file:
        return UserProfile.from_dict(json.load(file))


def _load_products(path: Path | None) -> list[Product]:
    if path is None:
        raise SystemExit("Pass --sample or --products products.json")
    with path.open("r", encoding="utf-8") as file:
        return [Product.from_dict(item) for item in json.load(file)]


if __name__ == "__main__":
    main()
