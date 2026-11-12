import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from models import Expense
from storage import JsonStorage, StorageError

logger = logging.getLogger(__name__)

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "expenses.json"
DATE_FORMAT = "%Y-%m-%d"


def format_expense(e: Expense | dict) -> str:
    d = e if isinstance(e, dict) else asdict(e)
    return (
        f"Amount: {d['amount']}, "
        f"Category: {d['category']}, "
        f"Description: {d['description']}, "
        f"Date: {d['date']}"
    )


class ExpenseManager:

    def __init__(self, storage: JsonStorage | None = None):
        self.storage = storage or JsonStorage(DEFAULT_PATH)
        self.expenses: list[Expense] = []
        logger.debug("ExpenseManager initialised, data file: %s", self.storage.filepath)

    @staticmethod
    def _validate(expense: Expense) -> None:
        if expense.amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        try:
            datetime.strptime(expense.date, DATE_FORMAT)
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format.") from None

    async def load(self) -> None:
        try:
            raw = await self.storage.load()
        except StorageError as e:
            print(f"{e} Starting with an empty list.")
            return

        loaded: list[Expense] = []
        for item in raw:
            try:
                expense = Expense(**item)
                self._validate(expense)       
            except (TypeError, ValueError):
                logger.warning("Skipping malformed record: %r", item)
                continue
            loaded.append(expense)

        self.expenses = loaded
        print(f"Loaded {len(loaded)} saved expenses.")

    def add_expense(self, expense: Expense) -> None:
        self._validate(expense)
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
        snapshot = [asdict(e) for e in self.expenses]
        try:
            await self.storage.save(snapshot)
        except StorageError as e:
            print(f"{e} Check the log file for details.")
            return
        print("Expenses saved.")

    async def view_all_expenses(self) -> None:
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