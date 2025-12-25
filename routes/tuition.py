from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from routes.auth import login_required
from routes.database import db, TuitionRecord
from flask_login import current_user
from datetime import datetime

tuition_bp = Blueprint('tuition', __name__)


@tuition_bp.route('/tuition')
@login_required
def tuition_list():
    """Display tuition records."""
    user_id = current_user.id

    # Get all tuition records for the user, sorted by most completed days first
    records = TuitionRecord.query.filter_by(
        user_id=user_id).order_by(TuitionRecord.total_completed.desc()).all()

    # Calculate statistics
    total_amount = sum(rec.amount for rec in records) if records else 0
    total_students = len(records)
    total_completed_classes = sum(
        rec.total_completed for rec in records) if records else 0
    total_classes = sum(rec.total_days for rec in records) if records else 0

    # Group tuitions by day of week
    schedule_by_day = {
        0: [],  # Sunday
        1: [],  # Monday
        2: [],  # Tuesday
        3: [],  # Wednesday
        4: [],  # Thursday
        5: [],  # Friday
        6: []   # Saturday
    }

    for record in records:
        if record.days:  # If days field exists
            for day in record.days:
                schedule_by_day[day].append(record)

    return render_template(
        'tuition.html',
        tuition_list=records,
        schedule_by_day=schedule_by_day,
        total_amount=total_amount,
        total_students=total_students,
        total_completed_classes=total_completed_classes,
        total_classes=total_classes
    )


@tuition_bp.route('/tuition/add', methods=['GET', 'POST'])
@login_required
def add_tuition():
    """Add a new tuition record."""
    if request.method == 'GET':
        return render_template('addTuition.html')

    user_id = current_user.id

    student_name = request.form.get('student_name')
    total_days = request.form.get('total_days')
    total_completed = request.form.get('total_completed', 0)
    address = request.form.get('address')
    amount = request.form.get('amount')
    tuition_time = request.form.get('tuition_time')  # Get the time field
    days = request.form.getlist('days')  # Get the selected days as a list

    # Validation
    if not all([student_name, total_days, address, amount]):
        flash('Please fill in all required fields!', 'error')
        return redirect(url_for('tuition.add_tuition'))

    try:
        amount = float(amount)
        total_days = int(total_days)
        total_completed = int(total_completed)
        if amount <= 0 or total_days <= 0 or total_completed < 0:
            raise ValueError("Amount and total days must be positive")
        if total_completed > total_days:
            raise ValueError("Completed days cannot exceed total days")
        # Convert days to integers
        days = [int(day) for day in days] if days else []
    except ValueError as e:
        flash(f'Invalid input: {str(e)}', 'error')
        return redirect(url_for('tuition.add_tuition'))

    # Add to database
    new_record = TuitionRecord(
        user_id=user_id,
        student_name=student_name,
        total_days=total_days,
        total_completed=total_completed,
        address=address,
        amount=amount,
        tuition_time=tuition_time if tuition_time else None,
        days=days if days else None
    )
    db.session.add(new_record)
    db.session.commit()

    flash('Tuition record added successfully!', 'success')
    return redirect(url_for('tuition.tuition_list'))


@tuition_bp.route('/tuition/update-completed/<int:record_id>/<action>', methods=['POST'])
@login_required
def update_completed(record_id, action):
    """Update completed days for a tuition record."""
    user_id = current_user.id

    # Find and verify ownership
    record = TuitionRecord.query.filter_by(
        id=record_id, user_id=user_id).first()

    if not record:
        flash('Record not found!', 'error')
        return redirect(url_for('tuition.tuition_list'))

    # Update completed days
    if action == 'increment' and record.total_completed < record.total_days:
        record.total_completed += 1
        db.session.commit()
        flash('Progress updated!', 'success')
    elif action == 'decrement' and record.total_completed > 0:
        record.total_completed -= 1
        db.session.commit()
        flash('Progress updated!', 'success')
    elif action == 'clear' and record.total_completed > 0:
        record.total_completed = 0
        db.session.commit()
        flash('Progress reset to 0!', 'success')
    else:
        flash('Cannot update progress!', 'error')

    return redirect(url_for('tuition.tuition_list'))


@tuition_bp.route('/tuition/delete/<int:record_id>', methods=['POST'])
@login_required
def delete_tuition(record_id):
    """Delete a tuition record."""
    user_id = current_user.id

    # Find and verify ownership
    record = TuitionRecord.query.filter_by(
        id=record_id, user_id=user_id).first()

    if not record:
        flash('Record not found!', 'error')
        return redirect(url_for('tuition.tuition_list'))

    # Delete record
    db.session.delete(record)
    db.session.commit()

    flash('Tuition record deleted successfully!', 'success')
    return redirect(url_for('tuition.tuition_list'))
