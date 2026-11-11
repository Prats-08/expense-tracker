import json
import logging

import pytest

from conftest import make_expense
from manager import ExpenseManager, format_expense
from models import Expense
from storage import JsonStorage


def test_format_expense_from_dataclass():
    e = make_expense(250, "Transport", "Cab", "2026-11-01")
    assert format_expense(e) == (
        "Amount: 250, Category: Transport, Description: Cab, Date: 2026-11-01"
    )


def test_format_expense_from_dict_matches_dataclass():
    e = make_expense(99, "Utilities", "WiFi", "2026-10-30")
    assert format_expense(e.__dict__) == format_expense(e)



def test_new_manager_starts_empty(manager):
    assert manager.expenses == []


def test_manager_uses_injected_storage(storage):
    assert ExpenseManager(storage).storage is storage


def test_add_expense_appends_to_list(manager):
    expense = make_expense()
    manager.add_expense(expense)
    assert manager.expenses == [expense]


def test_add_multiple_expenses_keeps_order(manager):
    first, second = make_expense(amount=10), make_expense(amount=20)
    manager.add_expense(first)
    manager.add_expense(second)
    assert manager.expenses == [first, second]


@pytest.mark.parametrize("amount", [0, -1, -0.01])
def test_add_expense_rejects_non_positive_amount(manager, amount):
    with pytest.raises(ValueError, match="greater than zero"):
        manager.add_expense(make_expense(amount=amount))
    assert manager.expenses == []


@pytest.mark.parametrize("bad_date", ["11-10-2026", "2026/11/10", "2026-13-01", "2026-02-30", "", "yesterday"])
def test_add_expense_rejects_bad_dates(manager, bad_date):
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        manager.add_expense(make_expense(date=bad_date))
    assert manager.expenses == []


def test_add_expense_accepts_leap_day(manager):
    manager.add_expense(make_expense(date="2028-02-29"))
    assert len(manager.expenses) == 1


def test_add_expense_logs_info(manager, caplog):
    with caplog.at_level(logging.INFO, logger="manager"):
        manager.add_expense(make_expense(amount=42))
    assert "Expense added" in caplog.text
    assert "amount=42" in caplog.text



def test_view_expenses_prints_each_expense(manager, capsys):
    manager.add_expense(make_expense(250, "Transport", "Cab", "2026-11-01"))
    manager.add_expense(make_expense(40, "Food", "Tea", "2026-11-02"))

    manager.view_expenses()

    lines = capsys.readouterr().out.strip().splitlines()
    assert lines == [
        "Amount: 250, Category: Transport, Description: Cab, Date: 2026-11-01",
        "Amount: 40, Category: Food, Description: Tea, Date: 2026-11-02",
    ]


def test_view_expenses_when_empty_says_so(manager, capsys):
    manager.view_expenses()
    assert capsys.readouterr().out.strip() == "No expenses in memory."


async def test_save_writes_expenses_as_json(manager, storage):
    manager.add_expense(make_expense(250, "Transport", "Cab", "2026-11-01"))

    await manager.save_expenses_to_file()

    saved = json.loads(storage.filepath.read_text())
    assert saved == [
        {"amount": 250, "category": "Transport", "description": "Cab", "date": "2026-11-01"}
    ]


async def test_save_with_no_expenses_writes_empty_list(manager, storage):
    await manager.save_expenses_to_file()
    assert json.loads(storage.filepath.read_text()) == []


async def test_save_overwrites_previous_file_contents(manager, storage):
    storage.filepath.write_text('[{"old": "data"}]')
    manager.add_expense(make_expense(5))

    await manager.save_expenses_to_file()

    saved = json.loads(storage.filepath.read_text())
    assert len(saved) == 1
    assert saved[0]["amount"] == 5
    assert "old" not in saved[0]


async def test_save_creates_missing_directory(manager, tmp_path):
    manager.storage = JsonStorage(tmp_path / "new_dir" / "expenses.json")
    await manager.save_expenses_to_file()
    assert (tmp_path / "new_dir" / "expenses.json").exists()


async def test_save_prints_confirmation(manager, capsys):
    await manager.save_expenses_to_file()
    assert "Expenses saved." in capsys.readouterr().out


async def test_save_failure_prints_message_instead_of_crashing(manager, tmp_path, capsys):
    blocker = tmp_path / "blocker"
    blocker.write_text("i am a file, not a folder")
    manager.storage = JsonStorage(blocker / "expenses.json")

    await manager.save_expenses_to_file()   # must not raise

    out = capsys.readouterr().out
    assert "Could not save expenses." in out
    assert "Expenses saved." not in out


async def test_save_does_not_leave_tmp_file_behind(manager, storage):
    manager.add_expense(make_expense())
    await manager.save_expenses_to_file()
    leftovers = [p.name for p in storage.filepath.parent.iterdir()]
    assert leftovers == ["expenses.json"]


async def test_view_all_expenses_prints_data_from_file(manager, storage, capsys):
    storage.filepath.write_text(json.dumps([
        {"amount": 99, "category": "Utilities", "description": "WiFi", "date": "2026-10-30"},
    ]))

    await manager.view_all_expenses()

    assert capsys.readouterr().out.strip() == (
        "Amount: 99, Category: Utilities, Description: WiFi, Date: 2026-10-30"
    )


async def test_view_all_expenses_reads_file_not_memory(manager, storage, capsys):
    manager.add_expense(make_expense(1, "Other", "x", "2026-01-01"))
    storage.filepath.write_text("[]")

    await manager.view_all_expenses()

    assert capsys.readouterr().out.strip() == "No saved expenses yet."


async def test_view_all_expenses_missing_file_says_no_saved_expenses(manager, capsys):
    await manager.view_all_expenses()
    assert capsys.readouterr().out.strip() == "No saved expenses yet."


async def test_view_all_expenses_corrupt_json_prints_error(manager, storage, capsys):
    storage.filepath.write_text("not json")
    await manager.view_all_expenses()
    assert "corrupted" in capsys.readouterr().out


async def test_load_populates_expenses(manager, storage, capsys):
    storage.filepath.write_text(json.dumps([
        {"amount": 10, "category": "Food", "description": "Snack", "date": "2026-11-01"},
        {"amount": 20, "category": "Rent", "description": "Room", "date": "2026-11-02"},
    ]))

    await manager.load()

    assert manager.expenses == [
        Expense(10, "Food", "Snack", "2026-11-01"),
        Expense(20, "Rent", "Room", "2026-11-02"),
    ]
    assert "Loaded 2 saved expenses." in capsys.readouterr().out


async def test_load_with_no_file_starts_empty(manager):
    await manager.load()
    assert manager.expenses == []


async def test_load_skips_malformed_records(manager, storage, caplog):
    storage.filepath.write_text(json.dumps([
        {"amount": 10, "category": "Food", "description": "ok", "date": "2026-11-01"},
        {"amount": 5},                                    # missing fields
        {"amount": 1, "category": "Food", "description": "x", "date": "2026-11-01", "extra": 1},
    ]))

    with caplog.at_level(logging.WARNING, logger="manager"):
        await manager.load()

    assert len(manager.expenses) == 1
    assert manager.expenses[0].description == "ok"
    assert caplog.text.count("Skipping malformed record") == 2


async def test_load_corrupt_file_starts_empty_and_tells_user(manager, storage, capsys):
    storage.filepath.write_text("{{{ broken")

    await manager.load()

    assert manager.expenses == []
    out = capsys.readouterr().out
    assert "corrupted" in out
    assert "Starting with an empty list." in out



async def test_save_then_view_all_round_trip(manager, capsys):
    manager.add_expense(make_expense(120, "Food", "Dinner", "2026-11-09"))
    await manager.save_expenses_to_file()
    capsys.readouterr()  

    await manager.view_all_expenses()

    assert capsys.readouterr().out.strip() == (
        "Amount: 120, Category: Food, Description: Dinner, Date: 2026-11-09"
    )


async def test_save_then_load_in_fresh_manager(manager, storage):
    manager.add_expense(make_expense(120, "Food", "Dinner", "2026-11-09"))
    manager.add_expense(make_expense(75.5, "Health", "Pharmacy", "2026-11-10"))
    await manager.save_expenses_to_file()

    fresh = ExpenseManager(JsonStorage(storage.filepath))
    await fresh.load()

    assert fresh.expenses == manager.expenses