from __future__ import annotations

import argparse
import json
from pathlib import Path

from gurkerl_recommender.config import AppConfig
from gurkerl_recommender.env import load_dotenv
from gurkerl_recommender.models import UserProfile
from gurkerl_recommender.scoring import recommend_products
from gurkerl_recommender.sources import build_product_source, enrich_gurkerl_public_details


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Debug product source parsing/scoring.")
    parser.add_argument("--config", type=Path, default=Path("config.public.example.json"))
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    config = AppConfig.from_file(args.config)
    source = build_product_source(config.source)
    products = source.fetch_products()
    with config.profile_path.open("r", encoding="utf-8") as file:
        profile = UserProfile.from_dict(json.load(file))
    initial_limit = max(args.limit, config.source.enrich_limit)
    recommendations = recommend_products(products, profile, limit=initial_limit)
    if config.source.type == "gurkerl_public" and config.source.enrich_details:
        enriched_products = enrich_gurkerl_public_details(
            [recommendation.product for recommendation in recommendations[: config.source.enrich_limit]]
        )
        recommendations = recommend_products(enriched_products, profile, limit=args.limit)

    print(f"products: {len(products)}")
    print(f"recommendations: {len(recommendations)}")
    for recommendation in recommendations:
        product = recommendation.product
        print(f"- {recommendation.score:g} | {product.name}")
        print(
            f"  category={product.category} promo={product.is_promotion} "
            f"save_food={product.is_save_food} discount={product.discount_percent:g} "
            f"expires={product.expires_in_days} nutrition={product.nutrition_source}"
        )
        if product.detail_url:
            print(f"  detail: {product.detail_url}")
        print(f"  reasons: {'; '.join(recommendation.reasons)}")
        if recommendation.cautions:
            print(f"  cautions: {'; '.join(recommendation.cautions)}")


if __name__ == "__main__":
    main()
