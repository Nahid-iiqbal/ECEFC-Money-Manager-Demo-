from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from routes.auth import login_required
import database
from datetime import datetime

tuition_bp = Blueprint('tuition', __name__)


@tuition_bp.route('/tuition')
@login_required
def tuition_list():
    """Display tuition records."""
    user_id = session.get('user_id')
    
    conn = database.get_db_connection()
    records = conn.execute(
        '''SELECT * FROM tuition_records 
           WHERE user_id = ? 
           ORDER BY due_date DESC, created_at DESC''',
        (user_id,)
    ).fetchall()
    
    # Calculate statistics
    total_amount = sum(rec['amount'] for rec in records)
    total_paid = sum(rec['paid_amount'] for rec in records)
    total_due = total_amount - total_paid
    
    pending_count = len([r for r in records if r['status'] == 'pending'])
    paid_count = len([r for r in records if r['status'] == 'paid'])
    
    conn.close()
    
    return render_template(
        'tuition.html',
        records=records,
        total_amount=total_amount,
        total_paid=total_paid,
        total_due=total_due,
        pending_count=pending_count,
        paid_count=paid_count
    )


@tuition_bp.route('/tuition/add', methods=['POST'])
@login_required
def add_tuition():
    """Add a new tuition record."""
    user_id = session.get('user_id')
    
    semester = request.form.get('semester')
    amount = request.form.get('amount')
    due_date = request.form.get('due_date')
    notes = request.form.get('notes', '')
    
    # Validation
    if not all([semester, amount, due_date]):
        flash('Please fill in all required fields!', 'error')
        return redirect(url_for('tuition.tuition_list'))
    
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except ValueError:
        flash('Invalid amount!', 'error')
        return redirect(url_for('tuition.tuition_list'))
    
    # Add to database
    conn = database.get_db_connection()
    conn.execute(
        '''INSERT INTO tuition_records 
           (user_id, semester, amount, due_date, notes, status)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (user_id, semester, amount, due_date, notes, 'pending')
    )
    conn.commit()
    conn.close()
    
    flash('Tuition record added successfully!', 'success')
    return redirect(url_for('tuition.tuition_list'))


@tuition_bp.route('/tuition/update/<int:record_id>', methods=['POST'])
@login_required
def update_tuition(record_id):
    """Update a tuition record."""
    user_id = session.get('user_id')
    
    semester = request.form.get('semester')
    amount = request.form.get('amount')
    paid_amount = request.form.get('paid_amount', 0)
    due_date = request.form.get('due_date')
    status = request.form.get('status')
    notes = request.form.get('notes', '')
    
    # Validation
    if not all([semester, amount, due_date, status]):
        flash('Please fill in all required fields!', 'error')
        return redirect(url_for('tuition.tuition_list'))
    
    try:
        amount = float(amount)
        paid_amount = float(paid_amount)
        if amount <= 0 or paid_amount < 0:
            raise ValueError("Invalid amounts")
    except ValueError:
        flash('Invalid amount values!', 'error')
        return redirect(url_for('tuition.tuition_list'))
    
    conn = database.get_db_connection()
    
    # Verify ownership
    record = conn.execute(
        'SELECT * FROM tuition_records WHERE id = ? AND user_id = ?',
        (record_id, user_id)
    ).fetchone()
    
    if not record:
        conn.close()
        flash('Record not found!', 'error')
        return redirect(url_for('tuition.tuition_list'))
    
    # Update record
    conn.execute(
        '''UPDATE tuition_records 
           SET semester = ?, amount = ?, paid_amount = ?, 
               due_date = ?, status = ?, notes = ?
           WHERE id = ?''',
        (semester, amount, paid_amount, due_date, status, notes, record_id)
    )
    conn.commit()
    conn.close()
    
    flash('Tuition record updated successfully!', 'success')
    return redirect(url_for('tuition.tuition_list'))


@tuition_bp.route('/tuition/pay/<int:record_id>', methods=['POST'])
@login_required
def make_payment(record_id):
    """Make a payment towards tuition."""
    user_id = session.get('user_id')
    payment_amount = request.form.get('payment_amount')
    
    if not payment_amount:
        flash('Payment amount is required!', 'error')
        return redirect(url_for('tuition.tuition_list'))
    
    try:
        payment_amount = float(payment_amount)
        if payment_amount <= 0:
            raise ValueError("Amount must be positive")
    except ValueError:
        flash('Invalid payment amount!', 'error')
        return redirect(url_for('tuition.tuition_list'))
    
    conn = database.get_db_connection()
    
    # Verify ownership
    record = conn.execute(
        'SELECT * FROM tuition_records WHERE id = ? AND user_id = ?',
        (record_id, user_id)
    ).fetchone()
    
    if not record:
        conn.close()
        flash('Record not found!', 'error')
        return redirect(url_for('tuition.tuition_list'))
    
    # Update paid amount
    new_paid_amount = record['paid_amount'] + payment_amount
    new_status = 'paid' if new_paid_amount >= record['amount'] else 'partial'
    
    conn.execute(
        '''UPDATE tuition_records 
           SET paid_amount = ?, status = ?
           WHERE id = ?''',
        (new_paid_amount, new_status, record_id)
    )
    conn.commit()
    conn.close()
    
    flash(f'Payment of {payment_amount} recorded successfully!', 'success')
    return redirect(url_for('tuition.tuition_list'))


@tuition_bp.route('/tuition/delete/<int:record_id>', methods=['POST'])
@login_required
def delete_tuition(record_id):
    """Delete a tuition record."""
    user_id = session.get('user_id')
    
    conn = database.get_db_connection()
    
    # Verify ownership
    record = conn.execute(
        'SELECT * FROM tuition_records WHERE id = ? AND user_id = ?',
        (record_id, user_id)
    ).fetchone()
    
    if not record:
        conn.close()
        flash('Record not found!', 'error')
        return redirect(url_for('tuition.tuition_list'))
    
    # Delete record
    conn.execute('DELETE FROM tuition_records WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()
    
    flash('Tuition record deleted successfully!', 'success')
    return redirect(url_for('tuition.tuition_list'))


@tuition_bp.route('/tuition/stats')
@login_required
def get_stats():
    """Get tuition statistics as JSON."""
    user_id = session.get('user_id')
    
    conn = database.get_db_connection()
    records = conn.execute(
        'SELECT * FROM tuition_records WHERE user_id = ?',
        (user_id,)
    ).fetchall()
    conn.close()
    
    total_amount = sum(rec['amount'] for rec in records)
    total_paid = sum(rec['paid_amount'] for rec in records)
    
    status_counts = {}
    for rec in records:
        status = rec['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return jsonify({
        'total_amount': total_amount,
        'total_paid': total_paid,
        'total_due': total_amount - total_paid,
        'status_counts': status_counts
    })
