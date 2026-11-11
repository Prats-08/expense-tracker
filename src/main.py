import asyncio
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from models import Expense, CATEGORIES
from manager import ExpenseManager
from reports import Report

logger = logging.getLogger(__name__)

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"

MENU = (
    "\nEnter your choice:\n"
    "1. Add Expense\n"
    "2. View Expenses\n"
    "3. Show All Expenses\n"
    "4. Save All Previous Expenses\n"
    "5. Show Reports\n"
    "6. Exit\n"
)


def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        LOG_DIR / "expense_tracker.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    ))

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(handler)

def choose_category() -> str | None:
    """Numbered picker. Returns the chosen category, or None if cancelled."""
    while True:
        print("\nSelect a category:")
        for i, name in enumerate(CATEGORIES, start=1):
            print(f"{i}. {name}")

        raw = input("Choice (Enter to cancel): ").strip()
        if not raw:
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(CATEGORIES):
            return CATEGORIES[int(raw) - 1]
        print(f"Please enter a number from 1 to {len(CATEGORIES)}.")

def show_reports(expenses) -> None:
    if not expenses:
        print("No expenses to report on.")
        return
    report = Report(expenses)

    print(f"\nTotal spent: {report.total():.2f}")
    print(f"Average per day: {report.average_per_day():.2f}")

    print("\nBy category:")
    for cat, amt in report.by_category().items():
        print(f"  {cat:<15} {amt:>10.2f}")

    print("\nBy month:")
    for month, amt in report.by_month().items():
        print(f"  {month:<15} {amt:>10.2f}")

    print("\nTop 5 expenses:")
    for e in report.top_expenses(5):
        print(f"  {e.amount:>10.2f}  {e.category:<15} {e.description} ({e.date})")

async def main():
    setup_logging()
    logger.info("Expense tracker started")
    manager = ExpenseManager()
    await manager.load()                      

    while True:
        try:
            choice = int(input(MENU))   
        except ValueError:
            logger.warning("Non-numeric menu choice entered")
            print("Please enter a number from 1 to 5.")
            continue

        logger.debug("Menu choice selected: %d", choice)

        match choice:
            case 1:
                try:
                    amount = float(input("Enter amount: "))
                except ValueError:
                    print("Amount must be a number.")
                    continue

                category = choose_category()
                if category is None:
                    print("Cancelled.")
                    continue

                try:
                    manager.add_expense(Expense(
                        amount=amount,
                        category=category,
                        description=input("Enter description: "),
                        date=input("Enter date (YYYY-MM-DD): "),
                    ))
                except ValueError as e:
                    print(e)
                    continue
                print("Expense added.")                        
            case 2:
                manager.view_expenses()
            case 3:
                await manager.view_all_expenses()      
            case 4:
                await manager.save_expenses_to_file()
            case 5:
                show_reports(manager.expenses)
            case 6:
                logger.info("Expense tracker exiting normally")
                print("Exiting...")
                break
            case _:
                logger.warning("Invalid menu choice: %d", choice)
                print("Invalid choice. Please try again.")


if __name__ == "__main__":
    try:
        asyncio.run(main())                   
    except KeyboardInterrupt:
        logger.info("Interrupted by user (Ctrl+C)")
    except Exception:
        logger.critical("Unhandled exception, app crashed", exc_info=True)
        raise