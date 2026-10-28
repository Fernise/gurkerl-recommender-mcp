from __future__ import annotations

import argparse
from pathlib import Path

from gurkerl_recommender.order_history import load_history
from gurkerl_recommender.weekly import WeeklyPlan, build_weekly_plan


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a weekly Gurkerl plan from order history.")
    parser.add_argument("history", nargs="+", type=Path)
    parser.add_argument("--budget-min", type=float, default=200)
    parser.add_argument("--budget-max", type=float, default=250)
    parser.add_argument("--cycle-days", type=int, default=9)
    args = parser.parse_args()

    plan = build_weekly_plan(
        load_history(args.history),
        monthly_budget_min=args.budget_min,
        monthly_budget_max=args.budget_max,
        cycle_days=args.cycle_days,
    )
    print(format_weekly_plan(plan))


def format_weekly_plan(plan: WeeklyPlan) -> str:
    lines = [
        "July Gurkerl weekly plan",
        f"Monthly budget: EUR {plan.budget_min:g}-{plan.budget_max:g}",
        f"Target per {plan.cycle_days} days: EUR {plan.target_cycle_budget_min:g}-{plan.target_cycle_budget_max:g}",
        "",
        "Staples",
    ]
    lines.extend(_format_items(plan.staples))
    lines.append("")
    lines.append("Flexible deals")
    lines.extend(_format_items(plan.flexible_deals))
    lines.append("")
    lines.append("Limit / skip in July")
    lines.extend(_format_items(plan.limit_or_skip))
    lines.append("")
    lines.append("Notes")
    lines.extend(f"- {note}" for note in plan.notes)
    return "\n".join(lines)


def _format_items(items: tuple) -> list[str]:
    return [
        f"- {item.name} ({item.typical_quantity}, avg EUR {item.avg_price:g}, seen {item.frequency}x)"
        for item in items
    ] or ["- none"]


if __name__ == "__main__":
    main()
