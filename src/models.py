from dataclasses import dataclass
from datetime import date as Date     

@dataclass
class Expense:
    amount: float
    category: str
    description: str
    date: Date

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