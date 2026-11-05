from models import Expense
import json
expenses : list[Expense] = []
filepath = "../../data/expenses.json"
def add_expense(expense: Expense):
    expenses.append(expense)

def view_expenses():
    for expense in expenses:
        print(f"Amount: {expense.amount}, Category: {expense.category}, Description: {expense.description}, Date: {expense.date}")

def save_expenses_to_file():
    with open(filepath, "w") as file:
        json.dump([expense.__dict__ for expense in expenses], file, indent=4)

def view_all_expenses():
    with open(filepath, "r") as file:
        data = json.load(file)
    for item in data:
        print(f"Amount: {item['amount']}, Category: {item['category']}, Description: {item['description']}, Date: {item['date']}")