"""Nutrition-aware product recommendations for Gurkerl shopping."""

from gurkerl_recommender.models import Nutrition, Product, UserProfile
from gurkerl_recommender.scoring import Recommendation, recommend_products

__all__ = [
    "Nutrition",
    "Product",
    "Recommendation",
    "UserProfile",
    "recommend_products",
]
