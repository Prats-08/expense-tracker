from models import Expense
from manager import add_expense, view_expenses, save_expenses_to_file, view_all_expenses
while(True):
    choice = int(input("Enter your choice: /n1. Add Expense/n2. View Expenses/n3. Show All Expenses/n4. Save All Previous Expenses/n5. Exit/n"))
    match(choice):
        case 1:
            expense = Expense(amount=float(input("Enter amount: ")),
                category=input("Enter category: "),
                description=input("Enter description: "),
                date=input("Enter date (YYYY-MM-DD): "))
            add_expense(expense)
        case 2:
            view_expenses()
        case 3:
            view_all_expenses()
        case 4:
            save_expenses_to_file()
        case 5:
            print("Exiting...")
            break
        case _:
            print("Invalid choice. Please try again.")
