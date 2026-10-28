from __future__ import annotations

from dataclasses import dataclass

from gurkerl_recommender.models import Product, UserProfile


@dataclass(frozen=True)
class Recommendation:
    product: Product
    score: float
    reasons: tuple[str, ...]
    cautions: tuple[str, ...]


def recommend_products(
    products: list[Product],
    profile: UserProfile,
    limit: int = 10,
) -> list[Recommendation]:
    recommendations = [_score_product(product, profile) for product in products]
    recommendations = [
        recommendation
        for recommendation in recommendations
        if not _is_blocked(recommendation.product, profile)
    ]
    return sorted(recommendations, key=lambda item: item.score, reverse=True)[:limit]


def _score_product(product: Product, profile: UserProfile) -> Recommendation:
    score = 0.0
    reasons: list[str] = []
    cautions: list[str] = []
    nutrition = product.nutrition_per_100g

    if product.category in profile.high_priority_categories:
        score += 18
        reasons.append(f"{product.category} is a high-priority category")
    elif product.category in profile.medium_priority_categories:
        score += 8
        reasons.append(f"{product.category} fits regular shopping")

    if nutrition.protein_g is not None:
        protein_score = min(nutrition.protein_g * 1.8, 45)
        score += protein_score
        if nutrition.protein_g >= profile.min_protein_per_100g:
            reasons.append(f"high protein ({nutrition.protein_g:g}g per 100g)")
        else:
            cautions.append(f"modest protein ({nutrition.protein_g:g}g per 100g)")

    if nutrition.sugar_g is not None:
        if nutrition.sugar_g <= profile.max_sugar_per_100g:
            score += 14
            reasons.append(f"low sugar ({nutrition.sugar_g:g}g per 100g)")
        else:
            penalty = min((nutrition.sugar_g - profile.max_sugar_per_100g) * 2, 30)
            score -= penalty
            cautions.append(f"sugar is high ({nutrition.sugar_g:g}g per 100g)")

    if nutrition.calories is not None:
        if profile.prefer_calories_min <= nutrition.calories <= profile.prefer_calories_max:
            score += 6
            reasons.append("calories fit a gym-friendly meal plan")
        elif nutrition.calories > profile.prefer_calories_max:
            cautions.append("calorie dense; useful only if portion is controlled")

    if profile.prefer_promotions and product.is_promotion:
        promo_bonus = 8 + min(product.discount_percent / 3, 12)
        score += promo_bonus
        reasons.append(f"promotion ({product.discount_percent:g}% off)")

    if profile.prefer_save_food and product.is_save_food:
        save_food_bonus = 14 + min(product.discount_percent / 2, 20)
        score += save_food_bonus
        reasons.append(f"Save Food deal ({product.discount_percent:g}% off)")

    if (
        product.price > 0
        and nutrition.protein_g
        and nutrition.protein_g >= profile.min_protein_per_100g
    ):
        price_per_protein = product.price / nutrition.protein_g
        if price_per_protein <= 0.25:
            score += 10
            reasons.append("strong price per protein")
        elif price_per_protein >= 0.7:
            score -= 8
            cautions.append("expensive for the protein it gives")

    brand = (product.brand or "").lower()
    if brand in profile.liked_brands:
        score += 5
        reasons.append("brand you like")
    if brand in profile.disliked_brands:
        score -= 25
        cautions.append("brand you disliked before")

    if product.category in {"meat", "fish"} and product.expires_in_days is not None:
        if product.expires_in_days <= profile.max_expires_in_days_for_meat:
            if product.is_save_food or product.is_promotion:
                score += 8
                reasons.append("good expiring meat/fish candidate if cooked or frozen soon")
            cautions.append(f"expires in {product.expires_in_days} day(s)")
        elif product.is_save_food:
            reasons.append("Save Food item with a little more time to use")

    return Recommendation(
        product=product,
        score=round(score, 2),
        reasons=tuple(reasons),
        cautions=tuple(cautions),
    )


def _is_blocked(product: Product, profile: UserProfile) -> bool:
    text = f"{product.name} {' '.join(product.tags)}".lower()
    return any(keyword in text for keyword in profile.never_buy_keywords)
