import pytest

from manager import ExpenseManager
from models import Expense
from storage import JsonStorage


def make_expense(amount=100, category="Food", description="Lunch", date="2026-11-10"):
    return Expense(amount, category, description, date)


@pytest.fixture
def storage(tmp_path):
    """Storage pointing at a temp file, never your real data folder."""
    return JsonStorage(tmp_path / "expenses.json")


@pytest.fixture
def manager(storage):
    return ExpenseManager(storage)