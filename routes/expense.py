from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from routes.database import db, Expense

expense = Blueprint("expense", __name__)

expenses = {}  # In-memory list to store expenses for testing purposes
@expense.route('/expenses')
@login_required
def view_expenses():
    user_expenses = Expense.query.filter_by(
        user_id=current_user.id
    ).all()
    total =0
    for val in user_expenses:
        total += val.amount
    return render_template("expenses.html", expenses=user_expenses, total=total)

@expense.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    name = request.form['name']
    amount = float(request.form['amount'])
    new_expense = Expense(name=name, amount=amount, user_id=current_user.id)
    db.session.add(new_expense)
    db.session.commit()

    return redirect(url_for('expense.view_expenses'))

@expense.route("/clear_expenses", methods=['POST'])
@login_required
def clear_expenses():
    Expense.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()

    return redirect(url_for('expense.view_expenses'))

@expense.route('/expenses_pop', methods=['POST'])

@login_required
def clear_pop_expense():
    expense_id = int(request.form['id'])
    expense = Expense.query.filter_by(id = expense_id, user_id = current_user.id).first()

    if expense:
        db.session.delete(expense)
        db.session.commit()
    
    return redirect(url_for('expense.view_expenses'))