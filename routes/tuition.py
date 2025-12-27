from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, make_response
from routes.auth import login_required
from routes.database import db, TuitionRecord, TuitionReschedule
from flask_login import current_user
from datetime import datetime, timedelta
from io import BytesIO
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Try to register Luckiest Guy font for PDF branding
# If font file exists in static/fonts/, use it; otherwise fallback to Helvetica-Bold
BRAND_FONT = 'Helvetica-Bold'  # Default fallback
try:
    font_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                             'static', 'fonts', 'LuckiestGuy-Regular.ttf')
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('LuckiestGuy', font_path))
        BRAND_FONT = 'LuckiestGuy'
except Exception:
    pass  # Silently fallback to Helvetica-Bold

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

    # Get current date and day of week
    today = datetime.now().date()
    current_day_index = today.weekday()  # 0=Monday, 6=Sunday
    # Convert to our format: 0=Sunday, 1=Monday, ..., 6=Saturday
    current_day_index = (current_day_index + 1) % 7

    # Calculate dates for the current week (Sunday to Saturday)
    # Get Sunday of the current week
    days_since_sunday = (today.weekday() + 1) % 7
    week_start = today - timedelta(days=days_since_sunday)

    # Create list of dates for the week
    week_dates = []
    for i in range(7):
        week_dates.append(week_start + timedelta(days=i))

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

    # Reorder days to put current day first
    ordered_days = []
    for i in range(7):
        day_idx = (current_day_index + i) % 7
        ordered_days.append(day_idx)

    # Ensure dates progress linearly from today without wrapping
    ordered_dates = []
    for i in range(7):
        ordered_dates.append(today + timedelta(days=i))

    # Get recent rescheduled classes (pending and confirmed)
    record_ids = [rec.id for rec in records]
    recent_reschedules = TuitionReschedule.query.filter(
        TuitionReschedule.tuition_id.in_(record_ids),
        TuitionReschedule.reschedule_status.in_(['pending', 'confirmed'])
    ).order_by(TuitionReschedule.created_at.desc()).limit(10).all()

    return render_template(
        'tuition.html',
        tuition_list=records,
        schedule_by_day=schedule_by_day,
        ordered_days=ordered_days,
        ordered_dates=ordered_dates,
        recent_reschedules=recent_reschedules,
        total_amount=total_amount,
        total_students=total_students,
        total_completed_classes=total_completed_classes,
        total_classes=total_classes,
        now=datetime.now(),
        current_day_index=current_day_index,
        today=today
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
    try:
        if action == 'increment' and record.total_completed < record.total_days:
            record.total_completed += 1
            db.session.commit()
            flash('✅ Class marked as completed!', 'success')
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
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating progress: {str(e)}', 'error')

    return redirect(url_for('tuition.tuition_list'))


@tuition_bp.route('/tuition/edit/<int:record_id>', methods=['GET', 'POST'])
@login_required
def edit_tuition(record_id):
    """Edit an existing tuition record."""
    user_id = current_user.id

    # Find and verify ownership
    record = TuitionRecord.query.filter_by(
        id=record_id, user_id=user_id).first()

    if not record:
        flash('Record not found!', 'error')
        return redirect(url_for('tuition.tuition_list'))

    if request.method == 'GET':
        return render_template('editTuition.html', record=record)

    # Handle POST request
    student_name = request.form.get('student_name')
    total_days = request.form.get('total_days')
    total_completed = request.form.get('total_completed', 0)
    address = request.form.get('address')
    amount = request.form.get('amount')
    tuition_time = request.form.get('tuition_time')
    days = request.form.getlist('days')

    # Validation
    if not all([student_name, total_days, address, amount]):
        flash('Please fill in all required fields!', 'error')
        return redirect(url_for('tuition.edit_tuition', record_id=record_id))

    try:
        amount = float(amount)
        total_days = int(total_days)
        total_completed = int(total_completed)
        if amount <= 0 or total_days <= 0 or total_completed < 0:
            raise ValueError("Amount and total days must be positive")
        if total_completed > total_days:
            raise ValueError("Completed days cannot exceed total days")
        days = [int(day) for day in days] if days else []
    except ValueError as e:
        flash(f'Invalid input: {str(e)}', 'error')
        return redirect(url_for('tuition.edit_tuition', record_id=record_id))

    # Update record
    record.student_name = student_name
    record.total_days = total_days
    record.total_completed = total_completed
    record.address = address
    record.amount = amount
    record.tuition_time = tuition_time if tuition_time else None
    record.days = days if days else None

    db.session.commit()

    flash('Tuition record updated successfully!', 'success')
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


@tuition_bp.route('/tuition/reschedule/<int:record_id>', methods=['GET', 'POST'])
@login_required
def reschedule_class(record_id):
    """Reschedule a class for a tuition record."""
    user_id = current_user.id

    # Find and verify ownership
    record = TuitionRecord.query.filter_by(
        id=record_id, user_id=user_id).first()

    if not record:
        flash('Record not found!', 'error')
        return redirect(url_for('tuition.tuition_list'))

    if request.method == 'GET':
        # Get reschedule history for this tuition
        reschedules = TuitionReschedule.query.filter_by(
            tuition_id=record_id).order_by(TuitionReschedule.created_at.desc()).all()
        return render_template('reschedule.html', record=record, reschedules=reschedules)

    # Handle POST request
    original_date = request.form.get('original_date')
    new_date = request.form.get('new_date')
    original_time = request.form.get('original_time')
    new_time = request.form.get('new_time')
    reason = request.form.get('reason', '')

    # Validation
    if not all([original_date, new_date, original_time, new_time]):
        flash('Please fill in all required fields!', 'error')
        return redirect(url_for('tuition.reschedule_class', record_id=record_id))

    try:
        original_date_obj = datetime.strptime(original_date, '%Y-%m-%d').date()
        new_date_obj = datetime.strptime(new_date, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format!', 'error')
        return redirect(url_for('tuition.reschedule_class', record_id=record_id))

    # Create reschedule record
    reschedule = TuitionReschedule(
        tuition_id=record_id,
        original_date=original_date_obj,
        new_date=new_date_obj,
        original_time=original_time,
        new_time=new_time,
        reason=reason,
        reschedule_status='pending'
    )
    db.session.add(reschedule)
    db.session.commit()

    flash('Class reschedule request created! Status: Pending', 'success')
    return redirect(url_for('tuition.tuition_list'))


@tuition_bp.route('/tuition/reschedule/edit/<int:reschedule_id>', methods=['GET', 'POST'])
@login_required
def edit_reschedule(reschedule_id):
    """Edit an existing reschedule request."""
    user_id = current_user.id

    # Find reschedule and verify ownership through tuition record
    reschedule = TuitionReschedule.query.get(reschedule_id)

    if not reschedule or reschedule.tuition.user_id != user_id:
        flash('Reschedule not found!', 'error')
        return redirect(url_for('tuition.tuition_list'))

    record = reschedule.tuition

    if request.method == 'GET':
        return render_template('edit_reschedule.html', record=record, reschedule=reschedule)

    # Handle POST request
    original_date = request.form.get('original_date')
    new_date = request.form.get('new_date')
    original_time = request.form.get('original_time')
    new_time = request.form.get('new_time')
    reason = request.form.get('reason', '')

    # Validation
    if not all([original_date, new_date, original_time, new_time]):
        flash('Please fill in all required fields!', 'error')
        return redirect(url_for('tuition.edit_reschedule', reschedule_id=reschedule_id))

    try:
        original_date_obj = datetime.strptime(original_date, '%Y-%m-%d').date()
        new_date_obj = datetime.strptime(new_date, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format!', 'error')
        return redirect(url_for('tuition.edit_reschedule', reschedule_id=reschedule_id))

    # Update reschedule record
    reschedule.original_date = original_date_obj
    reschedule.new_date = new_date_obj
    reschedule.original_time = original_time
    reschedule.new_time = new_time
    reschedule.reason = reason

    db.session.commit()

    flash('Reschedule updated successfully!', 'success')
    return redirect(url_for('tuition.tuition_list'))


@tuition_bp.route('/tuition/reschedule/confirm/<int:reschedule_id>', methods=['POST'])
@login_required
def confirm_reschedule(reschedule_id):
    """Confirm a reschedule request."""
    user_id = current_user.id

    # Find reschedule and verify ownership through tuition record
    reschedule = TuitionReschedule.query.get(reschedule_id)

    if not reschedule or reschedule.tuition.user_id != user_id:
        flash('Reschedule not found!', 'error')
        return redirect(url_for('tuition.tuition_list'))

    reschedule.reschedule_status = 'confirmed'
    db.session.commit()

    flash('Reschedule confirmed!', 'success')
    return redirect(url_for('tuition.reschedule_class', record_id=reschedule.tuition_id))


@tuition_bp.route('/tuition/reschedule/cancel/<int:reschedule_id>', methods=['POST'])
@login_required
def cancel_reschedule(reschedule_id):
    """Cancel a reschedule request."""
    user_id = current_user.id

    # Find reschedule and verify ownership through tuition record
    reschedule = TuitionReschedule.query.get(reschedule_id)

    if not reschedule or reschedule.tuition.user_id != user_id:
        flash('Reschedule not found!', 'error')
        return redirect(url_for('tuition.tuition_list'))

    reschedule.reschedule_status = 'cancelled'
    db.session.commit()

    flash('Reschedule cancelled!', 'info')
    return redirect(url_for('tuition.tuition_list'))


@tuition_bp.route('/tuition/reschedule/complete/<int:reschedule_id>', methods=['POST'])
@login_required
def mark_reschedule_completed(reschedule_id):
    """Mark a reschedule as completed and increment tuition progress."""
    user_id = current_user.id

    # Find reschedule and verify ownership through tuition record
    reschedule = TuitionReschedule.query.get(reschedule_id)

    if not reschedule or reschedule.tuition.user_id != user_id:
        flash('Reschedule not found!', 'error')
        return redirect(url_for('tuition.tuition_list'))

    try:
        # Mark reschedule as completed
        reschedule.reschedule_status = 'completed'

        # Increment the tuition progress if not already at max
        tuition_record = reschedule.tuition
        if tuition_record.total_completed < tuition_record.total_days:
            tuition_record.total_completed += 1

        db.session.commit()
        flash('Class marked as completed! Progress updated.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error marking class as completed: {str(e)}', 'error')

    return redirect(url_for('tuition.tuition_list'))


@tuition_bp.route('/tuition/export-pdf')
@login_required
def export_routine_pdf():
    """Export tuition routine as PDF."""
    user_id = current_user.id

    # Get all tuition records for the user
    records = TuitionRecord.query.filter_by(user_id=user_id).all()

    # Group tuitions by day of week
    schedule_by_day = {i: [] for i in range(7)}

    for record in records:
        # record.days is a list of integers (e.g., [0, 1, 3] for Sunday, Monday, Wednesday)
        if record.days:
            for day_idx in record.days:
                if isinstance(day_idx, int) and 0 <= day_idx <= 6:
                    schedule_by_day[day_idx].append(record)

    # Sort by time
    for day in schedule_by_day:
        schedule_by_day[day].sort(key=lambda x: x.tuition_time or "00:00")

    # Create PDF in landscape orientation for horizontal routine
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=30,
                            leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#e74c3c'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.grey,
        spaceAfter=20,
        alignment=TA_CENTER
    )

    # Title
    elements.append(Paragraph("🎓 Weekly Tuition Routine", title_style))
    elements.append(Paragraph(
        f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", subtitle_style))
    elements.append(Spacer(1, 0.3*inch))

    # Weekly Schedule Table
    days = ['Sunday', 'Monday', 'Tuesday',
            'Wednesday', 'Thursday', 'Friday', 'Saturday']

    # Prepare table data - Days as columns
    # First row: Day names
    header_row = days

    # Find the maximum number of classes on any day
    max_classes = max(len(schedule_by_day[day_idx]) for day_idx in range(7))
    if max_classes == 0:
        max_classes = 1  # At least one row for empty message

    # Initialize table data with header
    table_data = [header_row]

    # Create rows for each class slot
    for row_idx in range(max_classes):
        row = []
        for day_idx in range(7):
            day_classes = schedule_by_day[day_idx]
            if row_idx < len(day_classes):
                entry = day_classes[row_idx]
                # Create a formatted cell with student name, time, and address
                time_str = entry.tuition_time or "Time: N/A"
                address = entry.address[:20] + \
                    "..." if len(entry.address) > 20 else entry.address

                cell_content = Paragraph(
                    f"<b>{entry.student_name}</b><br/>"
                    f"<font size=9>⏰ {time_str}</font><br/>"
                    f"<font size=8>📍 {address}</font>",
                    ParagraphStyle(
                        'CellStyle',
                        parent=styles['Normal'],
                        fontSize=10,
                        leading=12,
                        alignment=TA_CENTER
                    )
                )
                row.append(cell_content)
            else:
                # Empty cell if no class at this time slot
                if row_idx == 0 and len(day_classes) == 0:
                    row.append(Paragraph("<i>No classes</i>",
                                         ParagraphStyle('EmptyStyle', parent=styles['Normal'],
                                                        fontSize=9, alignment=TA_CENTER, textColor=colors.grey)))
                else:
                    row.append('')
        table_data.append(row)

    # Create table with equal column widths for landscape orientation
    col_width = 10.5*inch / 7  # Distribute width evenly across 7 days in landscape
    table = Table(table_data, colWidths=[col_width] * 7,
                  rowHeights=[0.4*inch] + [1*inch] * max_classes)

    # Table style
    table_style = [
        # Header row (days)
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),

        # Data rows
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1.5, colors.HexColor('#cccccc')),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#4a90e2')),
    ]

    # Add alternating colors for data rows
    for row_idx in range(1, len(table_data)):
        if row_idx % 2 == 1:
            table_style.append(
                ('BACKGROUND', (0, row_idx),
                 (-1, row_idx), colors.HexColor('#f8f9fa'))
            )
        else:
            table_style.append(
                ('BACKGROUND', (0, row_idx), (-1, row_idx), colors.white)
            )

    # Add light background to cells with content
    for day_idx in range(7):
        for row_idx in range(1, len(table_data)):
            if schedule_by_day[day_idx] and (row_idx - 1) < len(schedule_by_day[day_idx]):
                table_style.append(
                    ('BACKGROUND', (day_idx, row_idx), (day_idx, row_idx),
                     colors.HexColor('#e3f2fd'))
                )

    table.setStyle(TableStyle(table_style))

    elements.append(table)
    elements.append(Spacer(1, 0.5*inch))

    # Summary statistics
    total_students = len(records)
    total_amount = sum(rec.amount for rec in records)
    total_classes = sum(rec.total_days for rec in records)

    summary_data = [
        ['Summary Statistics', ''],
        ['Total Students', str(total_students)],
        ['Total Income', f"{total_amount:,.2f} bdt."],
        ['Total Classes', str(total_classes)]
    ]

    summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('SPAN', (0, 0), (-1, 0)),

        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))

    elements.append(summary_table)

    # Branding: header/footer on each page
    def draw_branding(canvas_obj, doc_obj):
        width, height = landscape(A4)
        # Header bar
        canvas_obj.setFillColor(colors.HexColor('#667eea'))
        canvas_obj.rect(0, height - 25, width, 25, fill=1, stroke=0)
        # Brand text - use Luckiest Guy if available, else Helvetica-Bold
        canvas_obj.setFillColor(colors.whitesmoke)
        canvas_obj.setFont(BRAND_FONT, 16)
        canvas_obj.drawCentredString(width / 2, height - 18, 'FinBuddy')
        # Footer
        canvas_obj.setFillColor(colors.HexColor('#888888'))
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.drawString(
            30, 15, f"Generated on {datetime.now().strftime('%b %d, %Y')} • FinBuddy")
        canvas_obj.drawRightString(width - 30, 15, f"Page {doc_obj.page}")

    # Build PDF with branding
    doc.build(elements, onFirstPage=draw_branding, onLaterPages=draw_branding)

    # Get PDF from buffer
    pdf = buffer.getvalue()
    buffer.close()

    # Create response
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers[
        'Content-Disposition'] = f'attachment; filename=Weekly_Routine_for_{current_user.username}.pdf'

    return response
