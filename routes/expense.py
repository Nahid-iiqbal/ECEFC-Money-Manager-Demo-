from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from routes.database import db, Expense
from datetime import datetime
from sqlalchemy import extract, func

expense = Blueprint("expense", __name__)

@expense.route('/personal')
@login_required
def personal():
    """Display personal expenses dashboard (aliased from /expenses)."""
    user_expenses = Expense.query.filter_by(
        user_id=current_user.id
    ).order_by(Expense.date.desc(), Expense.created_at.desc()).all()
    
    total = sum(exp.amount for exp in user_expenses)
    
    # Category breakdown
    category_totals = {}
    for exp in user_expenses:
        category = exp.category
        category_totals[category] = category_totals.get(category, 0) + exp.amount
    
    return render_template(
        "expenses.html", 
        expenses=user_expenses, 
        total=total,
        category_totals=category_totals
    )

@expense.route('/expenses')
@login_required
def view_expenses():
    """Redirect to personal expenses."""
    return redirect(url_for('expense.personal'))

@expense.route('/personal/add', methods=['POST'])
@login_required
def add_expense():
    """Add a new personal expense."""
    try:
        name = request.form.get('name') or request.form.get('title')
        amount = float(request.form.get('amount', 0))
        category = request.form.get('category', 'Other')
        description = request.form.get('description', '')
        date_str = request.form.get('date')
        
        # Parse date or use today
        if date_str:
            expense_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            expense_date = datetime.utcnow().date()
        
        new_expense = Expense(
            name=name,
            amount=amount,
            category=category,
            description=description,
            date=expense_date,
            user_id=current_user.id
        )
        db.session.add(new_expense)
        db.session.commit()
        
        flash('Expense added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding expense: {str(e)}', 'danger')
    
    return redirect(url_for('expense.personal'))

@expense.route('/add_expense', methods=['POST'])
@login_required
def add_expense_legacy():
    """Legacy route for adding expenses."""
    return add_expense()

@expense.route("/clear_expenses", methods=['POST'])
@login_required
def clear_expenses():
    """Delete all expenses for current user."""
    try:
        Expense.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        flash('All expenses cleared!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error clearing expenses: {str(e)}', 'danger')
    
    return redirect(url_for('expense.personal'))

@expense.route('/expenses_pop', methods=['POST'])
@login_required
def clear_pop_expense():
    """Delete a specific expense."""
    return delete_expense()

@expense.route('/personal/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id=None):
    """Delete a specific personal expense."""
    try:
        if expense_id is None:
            expense_id = int(request.form.get('id'))
        
        expense_to_delete = Expense.query.filter_by(
            id=expense_id, 
            user_id=current_user.id
        ).first()
        
        if expense_to_delete:
            db.session.delete(expense_to_delete)
            db.session.commit()
            flash('Expense deleted successfully!', 'success')
        else:
            flash('Expense not found!', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting expense: {str(e)}', 'danger')
    
    return redirect(url_for('expense.personal'))

@expense.route('/personal/update/<int:expense_id>', methods=['POST'])
@login_required
def update_expense(expense_id):
    """Update an existing personal expense."""
    try:
        expense_to_update = Expense.query.filter_by(
            id=expense_id,
            user_id=current_user.id
        ).first()
        
        if expense_to_update:
            expense_to_update.name = request.form.get('name', expense_to_update.name)
            expense_to_update.amount = float(request.form.get('amount', expense_to_update.amount))
            expense_to_update.category = request.form.get('category', expense_to_update.category)
            expense_to_update.description = request.form.get('description', expense_to_update.description)
            
            date_str = request.form.get('date')
            if date_str:
                expense_to_update.date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            db.session.commit()
            flash('Expense updated successfully!', 'success')
        else:
            flash('Expense not found!', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating expense: {str(e)}', 'danger')
    
    return redirect(url_for('expense.personal'))

@expense.route('/personal/stats')
@login_required
def expense_stats():
    """View expense statistics and analytics."""
    user_expenses = Expense.query.filter_by(user_id=current_user.id).all()
    
    # Monthly totals
    monthly_totals = db.session.query(
        extract('year', Expense.date).label('year'),
        extract('month', Expense.date).label('month'),
        func.sum(Expense.amount).label('total')
    ).filter_by(user_id=current_user.id).group_by('year', 'month').all()
    
    # Category totals
    category_totals = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('total'),
        func.count(Expense.id).label('count')
    ).filter_by(user_id=current_user.id).group_by(Expense.category).all()
    
    return render_template(
        'expense_stats.html',
        monthly_totals=monthly_totals,
        category_totals=category_totals,
        total_expenses=sum(exp.amount for exp in user_expenses)
    )