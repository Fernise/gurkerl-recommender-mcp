from __future__ import annotations

from typing import Any

from gurkerl_recommender.models import Product, UserProfile
from gurkerl_recommender.sample_data import SAMPLE_PRODUCTS
from gurkerl_recommender.scoring import Recommendation, recommend_products


def serialize_recommendation(recommendation: Recommendation) -> dict[str, Any]:
    product = recommendation.product
    return {
        "id": product.id,
        "name": product.name,
        "category": product.category,
        "brand": product.brand,
        "price": product.price,
        "size": product.size,
        "score": recommendation.score,
        "reasons": list(recommendation.reasons),
        "cautions": list(recommendation.cautions),
        "is_promotion": product.is_promotion,
        "is_save_food": product.is_save_food,
        "discount_percent": product.discount_percent,
        "expires_in_days": product.expires_in_days,
    }


def build_recommendations(
    products_payload: list[dict[str, Any]],
    profile_payload: dict[str, Any] | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    profile = UserProfile.from_dict(profile_payload or {})
    products = [Product.from_dict(item) for item in products_payload]
    return [
        serialize_recommendation(recommendation)
        for recommendation in recommend_products(products, profile, limit=limit)
    ]


def build_sample_recommendations(limit: int = 10) -> list[dict[str, Any]]:
    return [
        serialize_recommendation(recommendation)
        for recommendation in recommend_products(SAMPLE_PRODUCTS, UserProfile(), limit=limit)
    ]


try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover - optional runtime dependency
    FastMCP = None  # type: ignore[assignment]


if FastMCP is not None:
    mcp = FastMCP("gurkerl-recommender")

    @mcp.tool()
    def recommend_products_tool(
        products: list[dict[str, Any]],
        profile: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Rank Gurkerl product candidates for the user's goals."""
        return build_recommendations(products, profile, limit)

    @mcp.tool()
    def recommend_sample_products(limit: int = 10) -> list[dict[str, Any]]:
        """Return recommendations using local sample products."""
        return build_sample_recommendations(limit)


def main() -> None:
    if FastMCP is None:
        raise SystemExit("Install the optional MCP dependency first: pip install '.[mcp]'")
    mcp.run()


if __name__ == "__main__":
    main()
