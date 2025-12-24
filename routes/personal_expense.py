from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from routes.auth import login_required
import database
from datetime import datetime

personal_bp = Blueprint('personal', __name__)


@personal_bp.route('/personal')
@login_required
def personal():
    """Display personal expenses dashboard."""
    user_id = session.get('user_id')
    
    conn = database.get_db_connection()
    expenses = conn.execute(
        '''SELECT * FROM personal_expenses 
           WHERE user_id = ? 
           ORDER BY date DESC, created_at DESC''',
        (user_id,)
    ).fetchall()
    
    # Calculate statistics
    total_expenses = sum(exp['amount'] for exp in expenses)
    
    # Category breakdown
    category_totals = {}
    for exp in expenses:
        category = exp['category']
        category_totals[category] = category_totals.get(category, 0) + exp['amount']
    
    conn.close()
    
    return render_template(
        'personal.html',
        expenses=expenses,
        total_expenses=total_expenses,
        category_totals=category_totals
    )


@personal_bp.route('/personal/add', methods=['POST'])
@login_required
def add_expense():
    """Add a new personal expense."""
    user_id = session.get('user_id')
    
    title = request.form.get('title')
    amount = request.form.get('amount')
    category = request.form.get('category')
    description = request.form.get('description', '')
    date = request.form.get('date')
    
    # Validation
    if not all([title, amount, category, date]):
        flash('Please fill in all required fields!', 'error')
        return redirect(url_for('personal.personal'))
    
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except ValueError:
        flash('Invalid amount!', 'error')
        return redirect(url_for('personal.personal'))
    
    # Add to database
    conn = database.get_db_connection()
    conn.execute(
        '''INSERT INTO personal_expenses 
           (user_id, title, amount, category, description, date)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (user_id, title, amount, category, description, date)
    )
    conn.commit()
    conn.close()
    
    flash('Expense added successfully!', 'success')
    return redirect(url_for('personal.personal'))


@personal_bp.route('/personal/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    """Delete a personal expense."""
    user_id = session.get('user_id')
    
    conn = database.get_db_connection()
    
    # Verify ownership
    expense = conn.execute(
        'SELECT * FROM personal_expenses WHERE id = ? AND user_id = ?',
        (expense_id, user_id)
    ).fetchone()
    
    if not expense:
        conn.close()
        flash('Expense not found!', 'error')
        return redirect(url_for('personal.personal'))
    
    # Delete expense
    conn.execute('DELETE FROM personal_expenses WHERE id = ?', (expense_id,))
    conn.commit()
    conn.close()
    
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('personal.personal'))


@personal_bp.route('/personal/update/<int:expense_id>', methods=['POST'])
@login_required
def update_expense(expense_id):
    """Update a personal expense."""
    user_id = session.get('user_id')
    
    title = request.form.get('title')
    amount = request.form.get('amount')
    category = request.form.get('category')
    description = request.form.get('description', '')
    date = request.form.get('date')
    
    # Validation
    if not all([title, amount, category, date]):
        flash('Please fill in all required fields!', 'error')
        return redirect(url_for('personal.personal'))
    
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except ValueError:
        flash('Invalid amount!', 'error')
        return redirect(url_for('personal.personal'))
    
    conn = database.get_db_connection()
    
    # Verify ownership
    expense = conn.execute(
        'SELECT * FROM personal_expenses WHERE id = ? AND user_id = ?',
        (expense_id, user_id)
    ).fetchone()
    
    if not expense:
        conn.close()
        flash('Expense not found!', 'error')
        return redirect(url_for('personal.personal'))
    
    # Update expense
    conn.execute(
        '''UPDATE personal_expenses 
           SET title = ?, amount = ?, category = ?, description = ?, date = ?
           WHERE id = ?''',
        (title, amount, category, description, date, expense_id)
    )
    conn.commit()
    conn.close()
    
    flash('Expense updated successfully!', 'success')
    return redirect(url_for('personal.personal'))


@personal_bp.route('/personal/stats')
@login_required
def get_stats():
    """Get personal expense statistics as JSON."""
    user_id = session.get('user_id')
    
    conn = database.get_db_connection()
    expenses = conn.execute(
        'SELECT * FROM personal_expenses WHERE user_id = ?',
        (user_id,)
    ).fetchall()
    conn.close()
    
    # Calculate statistics
    total = sum(exp['amount'] for exp in expenses)
    count = len(expenses)
    
    categories = {}
    for exp in expenses:
        cat = exp['category']
        categories[cat] = categories.get(cat, 0) + exp['amount']
    
    return jsonify({
        'total': total,
        'count': count,
        'categories': categories
    })
