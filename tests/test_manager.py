import json

import pytest

from manager import ExpenseManager
from models import Expense


def make_expense(amount=100, category="Food", description="Lunch", date="2026-11-10"):
    return Expense(amount, category, description, date)


@pytest.fixture
def manager(tmp_path):
    """A manager that writes to a temp file, never your real data folder."""
    m = ExpenseManager()
    m.filepath = tmp_path / "expenses.json"
    return m


# ---------- add_expense ----------

def test_new_manager_starts_empty(manager):
    assert manager.expenses == []


def test_add_expense_appends_to_list(manager):
    expense = make_expense()
    manager.add_expense(expense)
    assert manager.expenses == [expense]


def test_add_multiple_expenses_keeps_order(manager):
    first = make_expense(amount=10)
    second = make_expense(amount=20)
    manager.add_expense(first)
    manager.add_expense(second)
    assert manager.expenses == [first, second]


# ---------- view_expenses ----------

def test_view_expenses_prints_each_expense(manager, capsys):
    manager.add_expense(make_expense(250, "Travel", "Cab", "2026-11-01"))
    manager.add_expense(make_expense(40, "Food", "Tea", "2026-11-02"))

    manager.view_expenses()

    lines = capsys.readouterr().out.strip().splitlines()
    assert lines == [
        "Amount: 250, Category: Travel, Description: Cab, Date: 2026-11-01",
        "Amount: 40, Category: Food, Description: Tea, Date: 2026-11-02",
    ]


def test_view_expenses_prints_nothing_when_empty(manager, capsys):
    manager.view_expenses()
    assert capsys.readouterr().out == ""


# ---------- save_expenses_to_file ----------

def test_save_writes_expenses_as_json(manager):
    manager.add_expense(make_expense(250, "Travel", "Cab", "2026-11-01"))

    manager.save_expenses_to_file()

    saved = json.loads(manager.filepath.read_text())
    assert saved == [
        {"amount": 250, "category": "Travel", "description": "Cab", "date": "2026-11-01"}
    ]


def test_save_with_no_expenses_writes_empty_list(manager):
    manager.save_expenses_to_file()
    assert json.loads(manager.filepath.read_text()) == []


def test_save_overwrites_previous_file_contents(manager):
    manager.filepath.write_text('[{"old": "data"}]')
    manager.add_expense(make_expense(5))

    manager.save_expenses_to_file()

    saved = json.loads(manager.filepath.read_text())
    assert len(saved) == 1
    assert saved[0]["amount"] == 5
    assert "old" not in saved[0]


def test_save_raises_if_directory_missing(manager, tmp_path):
    manager.filepath = tmp_path / "no_such_dir" / "expenses.json"
    with pytest.raises(FileNotFoundError):
        manager.save_expenses_to_file()


# ---------- view_all_expenses ----------

def test_view_all_expenses_prints_data_from_file(manager, capsys):
    manager.filepath.write_text(json.dumps([
        {"amount": 99, "category": "Bills", "description": "WiFi", "date": "2026-10-30"},
    ]))

    manager.view_all_expenses()

    out = capsys.readouterr().out.strip()
    assert out == "Amount: 99, Category: Bills, Description: WiFi, Date: 2026-10-30"


def test_view_all_expenses_reads_file_not_memory(manager, capsys):
    manager.add_expense(make_expense(1, "InMemory", "x", "2026-01-01"))
    manager.filepath.write_text("[]")

    manager.view_all_expenses()

    assert capsys.readouterr().out == ""


def test_view_all_expenses_missing_file_raises(manager):
    with pytest.raises(FileNotFoundError):
        manager.view_all_expenses()


def test_view_all_expenses_invalid_json_raises(manager):
    manager.filepath.write_text("not json")
    with pytest.raises(json.JSONDecodeError):
        manager.view_all_expenses()


# ---------- round trip ----------

def test_save_then_view_all_round_trip(manager, capsys):
    manager.add_expense(make_expense(120, "Food", "Dinner", "2026-11-09"))
    manager.save_expenses_to_file()

    manager.view_all_expenses()

    assert capsys.readouterr().out.strip() == (
        "Amount: 120, Category: Food, Description: Dinner, Date: 2026-11-09"
    )