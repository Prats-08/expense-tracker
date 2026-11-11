from dataclasses import dataclass
from datetime import date

@dataclass
class Expense:
    amount: float
    category: str
    description: str
    date: date

CATEGORIES = (
    "Food",
    "Transport",
    "Rent",
    "Utilities",
    "Shopping",
    "Health",
    "Entertainment",
    "Other",
)