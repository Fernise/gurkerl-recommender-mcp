from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

from gurkerl_recommender.order_history import HistoryItem


@dataclass(frozen=True)
class WeeklyRecommendation:
    name: str
    category: str
    typical_quantity: str
    avg_price: float
    frequency: int
    role: str


@dataclass(frozen=True)
class WeeklyPlan:
    budget_min: float
    budget_max: float
    cycle_days: int
    target_cycle_budget_min: float
    target_cycle_budget_max: float
    staples: tuple[WeeklyRecommendation, ...]
    flexible_deals: tuple[WeeklyRecommendation, ...]
    limit_or_skip: tuple[WeeklyRecommendation, ...]
    notes: tuple[str, ...]


def build_weekly_plan(
    items: list[HistoryItem],
    monthly_budget_min: float = 200,
    monthly_budget_max: float = 250,
    cycle_days: int = 9,
) -> WeeklyPlan:
    grouped = _group_items(items)
    recommendations = [
        _recommendation(name, values)
        for name, values in grouped.items()
    ]

    staples = tuple(
        item
        for item in sorted(recommendations, key=_staple_sort_key)
        if item.role == "staple"
    )[:14]
    flexible_deals = tuple(
        item
        for item in sorted(recommendations, key=_deal_sort_key)
        if item.role == "deal"
    )[:12]
    limit_or_skip = tuple(
        item
        for item in sorted(recommendations, key=_limit_sort_key)
        if item.role == "limit"
    )[:14]

    multiplier = cycle_days / 30
    return WeeklyPlan(
        budget_min=monthly_budget_min,
        budget_max=monthly_budget_max,
        cycle_days=cycle_days,
        target_cycle_budget_min=round(monthly_budget_min * multiplier, 2),
        target_cycle_budget_max=round(monthly_budget_max * multiplier, 2),
        staples=staples,
        flexible_deals=flexible_deals,
        limit_or_skip=limit_or_skip,
        notes=(
            "Use Save Food for meat/fish when it can be cooked or frozen soon.",
            "Keep non-food, alcohol, premium skincare, and snack items outside the food budget.",
            "Pay more for meat/fish only when exact nutrition, quality, or convenience clearly improves.",
        ),
    )


def _group_items(items: list[HistoryItem]) -> dict[str, list[HistoryItem]]:
    grouped: dict[str, list[HistoryItem]] = defaultdict(list)
    for item in items:
        grouped[canonical_name(item.name)].append(item)
    return grouped


def canonical_name(name: str) -> str:
    lowered = name.lower()
    if "eier aus freilandhaltung" in lowered:
        return "Eier aus Freilandhaltung M 10er"
    if "faschiertes gemischt" in lowered:
        return "Faschiertes gemischt"
    return name


def _recommendation(name: str, items: list[HistoryItem]) -> WeeklyRecommendation:
    category = categorize_product(name)
    avg_price = sum(item.price for item in items) / len(items)
    role = _role(name, category, len(items), avg_price)
    quantity = Counter(item.quantity for item in items).most_common(1)[0][0]
    return WeeklyRecommendation(
        name=name,
        category=category,
        typical_quantity=quantity,
        avg_price=round(avg_price, 2),
        frequency=len(items),
        role=role,
    )


def categorize_product(name: str) -> str:
    lowered = name.lower()
    if _is_processed_meat(lowered):
        return "processed_protein"
    if any(word in lowered for word in ("huhn", "chicken", "pute", "schwein", "karree", "faschiertes", "rind", "ribeye", "lachs", "thunfisch", "eier", "kebap")):
        return "protein"
    if any(word in lowered for word in ("skyr", "joghurt", "gouda", "mozzarella", "käse")):
        return "dairy"
    if any(word in lowered for word in ("reis", "pasta", "fusilli", "spaghetti", "toast", "hafer", "waffeln")):
        return "carbs"
    if any(word in lowered for word in ("bananen", "orangen", "salat", "gemüse", "gurke", "spinat")):
        return "fruit_veg"
    if any(word in lowered for word in ("cerave", "roche", "palmolive", "zahnpasta", "küchenrolle", "febreze", "salz")):
        return "household"
    if any(word in lowered for word in ("popcorn", "biscuits", "cracker", "pizza", "ottakringer")):
        return "snack_or_alcohol"
    return "other"


def _role(name: str, category: str, frequency: int, avg_price: float) -> str:
    lowered = name.lower()
    if category in {"household", "snack_or_alcohol"}:
        return "limit"
    if category == "processed_protein":
        return "deal" if avg_price <= 2.5 else "limit"
    if category in {"protein", "dairy", "carbs", "fruit_veg"} and frequency >= 3:
        return "staple"
    if category == "protein" and avg_price <= 6:
        return "deal"
    if category in {"dairy", "carbs", "fruit_veg"} and avg_price <= 3:
        return "deal"
    if any(word in lowered for word in ("ribeye", "premium", "pizza", "bier")):
        return "limit"
    return "deal"


def _staple_sort_key(item: WeeklyRecommendation) -> tuple[int, float]:
    priority = {"protein": 0, "dairy": 1, "carbs": 2, "fruit_veg": 3, "processed_protein": 4}
    return (priority.get(item.category, 9), -item.frequency)


def _deal_sort_key(item: WeeklyRecommendation) -> tuple[int, float]:
    priority = {"protein": 0, "dairy": 1, "carbs": 2, "fruit_veg": 3, "processed_protein": 4}
    return (priority.get(item.category, 9), item.avg_price)


def _limit_sort_key(item: WeeklyRecommendation) -> tuple[int, float]:
    return (-item.frequency, -item.avg_price)


def _is_processed_meat(lowered_name: str) -> bool:
    return any(
        word in lowered_name
        for word in (
            "schinken",
            "wiener",
            "würst",
            "wurst",
            "salami",
            "krainer",
            "debreziner",
        )
    )
