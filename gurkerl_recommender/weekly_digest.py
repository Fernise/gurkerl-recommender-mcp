from __future__ import annotations

import json
from dataclasses import dataclass
from html import escape
from pathlib import Path

from gurkerl_recommender.config import AppConfig
from gurkerl_recommender.models import UserProfile
from gurkerl_recommender.scoring import Recommendation, recommend_products
from gurkerl_recommender.sources import build_product_source, enrich_gurkerl_public_details


@dataclass(frozen=True)
class JulyBudgetProfile:
    monthly_budget_min: float
    monthly_budget_max: float
    cycle_days: int
    cycle_budget_min: float
    cycle_budget_max: float
    staples: tuple[str, ...]
    flexible_targets: tuple[str, ...]
    limit: tuple[str, ...]


def load_july_profile(path: Path) -> JulyBudgetProfile:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return JulyBudgetProfile(
        monthly_budget_min=float(payload["monthly_budget_eur"]["min"]),
        monthly_budget_max=float(payload["monthly_budget_eur"]["max"]),
        cycle_days=int(payload["shopping_cycle_days"]["typical"]),
        cycle_budget_min=float(payload["target_per_cycle_eur"]["min"]),
        cycle_budget_max=float(payload["target_per_cycle_eur"]["max"]),
        staples=tuple(payload["staples_from_history"]),
        flexible_targets=tuple(payload["flexible_deal_targets"]),
        limit=tuple(payload["limit_in_july"]),
    )


def build_weekly_digest(
    config: AppConfig,
    profile_path: Path = Path("profiles/july-budget-profile.json"),
    deal_limit: int = 6,
) -> str:
    july_profile = load_july_profile(profile_path)
    user_profile = _load_user_profile(config.profile_path)
    source = build_product_source(config.source)
    products = source.fetch_products()
    recommendations = recommend_products(
        products,
        user_profile,
        limit=max(config.source.enrich_limit, deal_limit),
    )
    if config.source.type == "gurkerl_public" and config.source.enrich_details:
        enriched = enrich_gurkerl_public_details(
            [recommendation.product for recommendation in recommendations[: config.source.enrich_limit]]
        )
        recommendations = recommend_products(enriched, user_profile, limit=deal_limit)
    else:
        recommendations = recommendations[:deal_limit]
    return format_weekly_digest(july_profile, recommendations)


def format_weekly_digest(
    profile: JulyBudgetProfile,
    deals: list[Recommendation],
) -> str:
    lines = [
        "🧺 <b>Gurkerl weekly basket</b>",
        f"💸 Budget: <b>EUR {profile.cycle_budget_min:g}-{profile.cycle_budget_max:g}</b> / {profile.cycle_days} days",
        "",
        "🏠 <b>Base staples</b>",
    ]
    lines.extend(f"▫️ {escape(item)}" for item in profile.staples[:8])
    lines.append("")
    lines.append("🔥 <b>Deals to consider today</b>")
    if deals:
        for recommendation in deals:
            product = recommendation.product
            name = escape(product.name)
            if product.detail_url:
                name = f'<a href="{escape(product.detail_url, quote=True)}">{name}</a>'
            lines.append(
                f"▫️ {name}\n"
                f"   💶 EUR {product.price:g} · 🎯 {recommendation.score:g} · 📊 {product.nutrition_source}"
            )
    else:
        lines.append("▫️ No strong deals found right now.")
    lines.append("")
    lines.append("🧘 <b>July discipline</b>")
    lines.extend(f"▫️ {escape(item)}" for item in profile.limit[:5])
    return "\n".join(lines)


def _load_user_profile(path: Path) -> UserProfile:
    with path.open("r", encoding="utf-8") as file:
        return UserProfile.from_dict(json.load(file))
