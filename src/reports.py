from collections import defaultdict
from datetime import datetime
from models import Expense, CATEGORIES

class Report:

    def __init__(self, expenses: list[Expense]):
        self.expenses = expenses

    def total(self) -> float:
        return round(sum(e.amount for e in self.expenses), 2)

    def by_category(self) -> dict[str, float]:
        totals = {c: 0.0 for c in CATEGORIES}
        for e in self.expenses:
            totals[e.category] = totals.get(e.category, 0.0) + e.amount
        rounded = {c: round(v, 2) for c, v in totals.items()}
        return dict(sorted(rounded.items(), key=lambda kv: kv[1], reverse=True))

    def by_month(self) -> dict[str, float]:
        totals: dict[str, float] = defaultdict(float)
        for e in self.expenses:
            totals[e.date[:7]] += e.amount
        return {m: round(v, 2) for m, v in sorted(totals.items())}

    def top_expenses(self, n: int = 5) -> list[Expense]:
        return sorted(self.expenses, key=lambda e: e.amount, reverse=True)[:n]

    def average_per_day(self) -> float:
        if not self.expenses:
            return 0.0
        dates = [datetime.strptime(e.date, "%Y-%m-%d").date() for e in self.expenses]
        days = (max(dates) - min(dates)).days + 1
        return round(self.total() / days, 2)