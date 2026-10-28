from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HistoryItem:
    name: str
    quantity: str
    price: float
    order_date: str


def load_history(paths: list[Path]) -> list[HistoryItem]:
    items: list[HistoryItem] = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for order in payload:
            order_date = str(order.get("fecha_pedido", ""))[:10]
            for product in order.get("productos", []):
                items.append(_history_item(product, order_date))
    return items


def _history_item(product: dict[str, Any], order_date: str) -> HistoryItem:
    return HistoryItem(
        name=str(product["nombre"]),
        quantity=str(product.get("cantidad", "")),
        price=float(product["precio"]),
        order_date=order_date,
    )
