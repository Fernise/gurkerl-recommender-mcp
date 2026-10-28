from __future__ import annotations

import json
from pathlib import Path

from gurkerl_recommender.config import AppConfig
from gurkerl_recommender.models import UserProfile
from gurkerl_recommender.notifiers import build_notifier
from gurkerl_recommender.scoring import Recommendation, recommend_products
from gurkerl_recommender.sources import build_product_source, enrich_gurkerl_public_details
from gurkerl_recommender.storage import RecommendationStore


def run_once(config: AppConfig) -> list[Recommendation]:
    profile = _load_profile(config.profile_path)
    source = build_product_source(config.source)
    products = source.fetch_products()
    initial_limit = max(config.recommendation_limit, config.source.enrich_limit)
    recommendations = recommend_products(
        products,
        profile,
        limit=initial_limit,
    )
    if config.source.type == "gurkerl_public" and config.source.enrich_details:
        enriched_products = enrich_gurkerl_public_details(
            [recommendation.product for recommendation in recommendations[: config.source.enrich_limit]]
        )
        recommendations = recommend_products(
            enriched_products,
            profile,
            limit=config.recommendation_limit,
        )

    notifier = build_notifier(config.notifier)
    notifications = _filter_notifications(config, recommendations)
    notifier.send(notifications)
    _record_recommendations(config, recommendations, notifications)
    return notifications


def _filter_notifications(
    config: AppConfig,
    recommendations: list[Recommendation],
) -> list[Recommendation]:
    notifications: list[Recommendation] = []
    with RecommendationStore(config.database_path) as store:
        for recommendation in recommendations:
            should_notify = recommendation.score >= config.notification_threshold
            if config.notify_only_new_products and store.has_notified(
                recommendation.product.id
            ):
                should_notify = False

            if should_notify:
                notifications.append(recommendation)
    return notifications


def _record_recommendations(
    config: AppConfig,
    recommendations: list[Recommendation],
    notifications: list[Recommendation],
) -> None:
    notified_ids = {recommendation.product.id for recommendation in notifications}
    with RecommendationStore(config.database_path) as store:
        for recommendation in recommendations:
            store.record_seen(
                recommendation,
                notified=recommendation.product.id in notified_ids,
            )


def _load_profile(path: Path) -> UserProfile:
    with path.open("r", encoding="utf-8") as file:
        return UserProfile.from_dict(json.load(file))
