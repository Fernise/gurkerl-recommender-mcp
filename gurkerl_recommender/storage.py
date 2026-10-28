from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from gurkerl_recommender.scoring import Recommendation


class RecommendationStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS recommendations (
                product_id TEXT PRIMARY KEY,
                product_name TEXT NOT NULL,
                score REAL NOT NULL,
                last_seen_at TEXT NOT NULL,
                notification_count INTEGER NOT NULL DEFAULT 0,
                last_payload TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def has_notified(self, product_id: str) -> bool:
        cursor = self.connection.execute(
            "SELECT notification_count FROM recommendations WHERE product_id = ?",
            (product_id,),
        )
        row = cursor.fetchone()
        return bool(row and row[0] > 0)

    def record_seen(self, recommendation: Recommendation, notified: bool) -> None:
        now = datetime.now(timezone.utc).isoformat()
        payload = json.dumps(
            {
                "reasons": recommendation.reasons,
                "cautions": recommendation.cautions,
                "price": recommendation.product.price,
                "discount_percent": recommendation.product.discount_percent,
                "is_promotion": recommendation.product.is_promotion,
                "is_save_food": recommendation.product.is_save_food,
                "expires_in_days": recommendation.product.expires_in_days,
            },
            sort_keys=True,
        )
        self.connection.execute(
            """
            INSERT INTO recommendations (
                product_id,
                product_name,
                score,
                last_seen_at,
                notification_count,
                last_payload
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(product_id) DO UPDATE SET
                product_name = excluded.product_name,
                score = excluded.score,
                last_seen_at = excluded.last_seen_at,
                notification_count = recommendations.notification_count
                    + excluded.notification_count,
                last_payload = excluded.last_payload
            """,
            (
                recommendation.product.id,
                recommendation.product.name,
                recommendation.score,
                now,
                1 if notified else 0,
                payload,
            ),
        )
        self.connection.commit()

    def __enter__(self) -> "RecommendationStore":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
