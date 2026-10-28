from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Nutrition:
    protein_g: float | None = None
    sugar_g: float | None = None
    calories: float | None = None
    fat_g: float | None = None
    carbs_g: float | None = None


@dataclass(frozen=True)
class Product:
    id: str
    name: str
    category: str
    price: float
    size: str | None = None
    brand: str | None = None
    nutrition_per_100g: Nutrition = field(default_factory=Nutrition)
    nutrition_source: str = "estimated"
    detail_url: str | None = None
    is_promotion: bool = False
    is_save_food: bool = False
    discount_percent: float = 0
    expires_in_days: int | None = None
    tags: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Product":
        nutrition_payload = payload.get("nutrition_per_100g", {})
        return cls(
            id=str(payload["id"]),
            name=str(payload["name"]),
            category=str(payload.get("category", "other")).lower(),
            price=float(payload["price"]),
            size=payload.get("size"),
            brand=payload.get("brand"),
            nutrition_per_100g=Nutrition(
                protein_g=_optional_float(nutrition_payload.get("protein_g")),
                sugar_g=_optional_float(nutrition_payload.get("sugar_g")),
                calories=_optional_float(nutrition_payload.get("calories")),
                fat_g=_optional_float(nutrition_payload.get("fat_g")),
                carbs_g=_optional_float(nutrition_payload.get("carbs_g")),
            ),
            nutrition_source=str(payload.get("nutrition_source", "estimated")),
            detail_url=payload.get("detail_url"),
            is_promotion=bool(payload.get("is_promotion", False)),
            is_save_food=bool(payload.get("is_save_food", False)),
            discount_percent=float(payload.get("discount_percent", 0)),
            expires_in_days=payload.get("expires_in_days"),
            tags=tuple(str(tag).lower() for tag in payload.get("tags", ())),
        )


@dataclass(frozen=True)
class UserProfile:
    min_protein_per_100g: float = 10
    max_sugar_per_100g: float = 6
    prefer_calories_min: float = 80
    prefer_calories_max: float = 260
    prefer_save_food: bool = True
    prefer_promotions: bool = True
    max_expires_in_days_for_meat: int = 2
    high_priority_categories: tuple[str, ...] = (
        "meat",
        "fish",
        "dairy",
        "eggs",
        "legumes",
    )
    medium_priority_categories: tuple[str, ...] = ("grains", "vegetables", "fruit")
    liked_brands: tuple[str, ...] = ()
    disliked_brands: tuple[str, ...] = ()
    never_buy_keywords: tuple[str, ...] = ("sugary drink", "candy")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "UserProfile":
        targets = payload.get("nutrition_targets", {})
        shopping = payload.get("shopping_preferences", {})
        categories = payload.get("category_preferences", {})
        return cls(
            min_protein_per_100g=float(targets.get("min_protein_per_100g", 10)),
            max_sugar_per_100g=float(targets.get("max_sugar_per_100g", 6)),
            prefer_calories_min=float(targets.get("prefer_calories_min", 80)),
            prefer_calories_max=float(targets.get("prefer_calories_max", 260)),
            prefer_save_food=bool(shopping.get("prefer_save_food", True)),
            prefer_promotions=bool(shopping.get("prefer_promotions", True)),
            max_expires_in_days_for_meat=int(
                shopping.get("max_expires_in_days_for_meat", 2)
            ),
            high_priority_categories=tuple(
                item.lower() for item in categories.get("high_priority", ())
            )
            or cls.high_priority_categories,
            medium_priority_categories=tuple(
                item.lower() for item in categories.get("medium_priority", ())
            )
            or cls.medium_priority_categories,
            liked_brands=tuple(
                item.lower() for item in payload.get("liked_brands", ())
            ),
            disliked_brands=tuple(
                item.lower() for item in payload.get("disliked_brands", ())
            ),
            never_buy_keywords=tuple(
                item.lower() for item in payload.get("never_buy_keywords", ())
            )
            or cls.never_buy_keywords,
        )


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
