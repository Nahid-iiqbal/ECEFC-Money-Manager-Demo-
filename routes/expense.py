from flask import Blueprint, render_template, request, redirect, url_for

expense = Blueprint("expense", __name__)

expenses = []  # In-memory list to store expenses for testing purposes
@expense.route('/expenses')
def view_expenses():
    return render_template("expenses.html", expenses=expenses)
@expense.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    name = request.form['name']
    amount = float(request.form['amount'])
    expenses.append({'name': name, 'amount': amount})
    return redirect(url_for('expense.view_expenses'))

@expense.route("/clear_expenses", methods=['POST'])
def clear_expenses():
    expenses.clear()
    return redirect(url_for('expense.view_expenses'))

@expense.route('/expenses_pop', methods=['POST'])
def clear_pop_expense():
    idx = int(request.form['idx'])
    expenses.pop(idx)
    return redirect(url_for('expense.view_expenses'))