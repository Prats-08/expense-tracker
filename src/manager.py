import logging
from datetime import datetime
from pathlib import Path

from models import Expense
from storage import JsonStorage, StorageError

logger = logging.getLogger(__name__)

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "expenses.json"


def format_expense(e) -> str:
    """e can be an Expense or a dict loaded from JSON."""
    get = e.get if isinstance(e, dict) else lambda k: getattr(e, k)
    return (
        f"Amount: {get('amount')}, "
        f"Category: {get('category')}, "
        f"Description: {get('description')}, "
        f"Date: {get('date')}"
    )


class ExpenseManager:

    def __init__(self, storage: JsonStorage | None = None):
        self.storage = storage or JsonStorage(DEFAULT_PATH)
        self.expenses: list[Expense] = []
        logger.debug("ExpenseManager initialised, data file: %s", self.storage.filepath)

    async def load(self) -> None:
        """Load previously saved expenses into memory. Call once at startup."""
        try:
            raw = await self.storage.load()
        except StorageError as e:
            print(f"{e} Starting with an empty list.")
            return

        loaded: list[Expense] = []
        for item in raw:
            try:
                loaded.append(Expense(**item))
            except TypeError:
                logger.warning("Skipping malformed record: %r", item)
        self.expenses = loaded
        print(f"Loaded {len(loaded)} saved expenses.")

    def add_expense(self, expense: Expense) -> None:
        """Validate and add. Raises ValueError with a user-friendly message."""
        if expense.amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        try:
            datetime.strptime(expense.date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format.") from None

        self.expenses.append(expense)
        logger.info(
            "Expense added: amount=%s category=%s date=%s (total in memory: %d)",
            expense.amount, expense.category, expense.date, len(self.expenses),
        )

    def view_expenses(self) -> None:
        if not self.expenses:
            logger.info("view_expenses called but no expenses in memory")
            print("No expenses in memory.")
            return

        logger.debug("Displaying %d in-memory expenses", len(self.expenses))
        for expense in self.expenses:
            print(format_expense(expense))

    async def save_expenses_to_file(self) -> None:
        snapshot = [e.__dict__.copy() for e in self.expenses]
        try:
            await self.storage.save(snapshot)
        except StorageError as e:
            print(f"{e} Check the log file for details.")
            return
        print("Expenses saved.")

    async def view_all_expenses(self) -> None:
        """Show what is currently saved on disk."""
        try:
            data = await self.storage.load()
        except StorageError as e:
            print(e)
            return

        if not data:
            print("No saved expenses yet.")
            return
        for item in data:
            print(format_expense(item))