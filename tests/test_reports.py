import pytest

from conftest import make_expense
from reports import Report


@pytest.fixture
def sample():
    return [
        make_expense(100, "Food", "Lunch", "2026-10-01"),
        make_expense(900, "Rent", "Room", "2026-10-05"),
        make_expense(50.555, "Food", "Tea", "2026-11-01"),
        make_expense(250, "Transport", "Cab", "2026-11-10"),
    ]


def test_total_sums_amounts(sample):
    assert Report(sample).total() == 1300.56


def test_total_of_empty_is_zero():
    assert Report([]).total() == 0


# ---------- by_category ----------

def test_by_category_sums_and_sorts_descending(sample):
    result = Report(sample).by_category()
    assert list(result)[:3] == ["Rent", "Transport", "Food"]
    assert result["Rent"] == 900
    assert result["Food"] == 150.56


def test_by_category_includes_all_known_categories_with_zero(sample):
    result = Report(sample).by_category()
    assert result["Health"] == 0
    assert result["Entertainment"] == 0


def test_by_category_keeps_unknown_category():
    result = Report([make_expense(10, "Gifts", "x", "2026-11-01")]).by_category()
    assert result["Gifts"] == 10



def test_by_month_groups_by_year_and_month(sample):
    assert Report(sample).by_month() == {"2026-10": 1000, "2026-11": 300.56}


def test_by_month_is_sorted_chronologically():
    expenses = [
        make_expense(1, date="2026-12-01"),
        make_expense(1, date="2026-01-15"),
        make_expense(1, date="2026-06-30"),
    ]
    assert list(Report(expenses).by_month()) == ["2026-01", "2026-06", "2026-12"]


def test_by_month_separates_same_month_different_years():
    expenses = [make_expense(5, date="2025-11-01"), make_expense(7, date="2026-11-01")]
    assert Report(expenses).by_month() == {"2025-11": 5, "2026-11": 7}


def test_by_month_empty():
    assert Report([]).by_month() == {}



def test_top_expenses_returns_largest_first(sample):
    top = Report(sample).top_expenses(2)
    assert [e.amount for e in top] == [900, 250]


def test_top_expenses_n_larger_than_list(sample):
    assert len(Report(sample).top_expenses(10)) == 4


def test_top_expenses_default_is_five():
    expenses = [make_expense(i + 1) for i in range(8)]
    assert len(Report(expenses).top_expenses()) == 5


def test_top_expenses_does_not_reorder_original_list(sample):
    before = list(sample)
    Report(sample).top_expenses(2)
    assert sample == before



def test_for_month_filters_expenses(sample):
    nov = Report(sample).for_month("2026-11")
    assert len(nov.expenses) == 2
    assert nov.total() == 300.56


def test_for_month_can_be_chained(sample):
    assert Report(sample).for_month("2026-10").by_category()["Rent"] == 900


def test_for_month_with_no_matches_is_empty(sample):
    assert Report(sample).for_month("1999-01").expenses == []


def test_average_per_day_over_date_span():
    expenses = [
        make_expense(100, date="2026-11-01"),
        make_expense(100, date="2026-11-10"),     
    ]
    assert Report(expenses).average_per_day() == 20.0


def test_average_per_day_single_day_is_total():
    expenses = [make_expense(30, date="2026-11-01"), make_expense(70, date="2026-11-01")]
    assert Report(expenses).average_per_day() == 100.0


def test_average_per_day_empty_is_zero():
    assert Report([]).average_per_day() == 0.0


def test_average_per_day_handles_unsorted_input():
    expenses = [make_expense(60, date="2026-11-03"), make_expense(60, date="2026-11-01")]
    assert Report(expenses).average_per_day() == 40.0   