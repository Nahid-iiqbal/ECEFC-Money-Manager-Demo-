from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, session
from flask_login import login_required, current_user, logout_user
from routes.database import db, Profile, Expense, User, Debt, GroupMember, GroupExpense, ExpenseSplit
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from datetime import datetime
import os
import csv
from io import StringIO

profile_bp = Blueprint('profile', __name__)

# Configuration for file uploads
UPLOAD_FOLDER = 'static/uploads/profiles'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def ensure_upload_folder():
    """Ensure upload folder exists"""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)


@profile_bp.route('/profile/create', methods=['GET', 'POST'])
@login_required
def create_profile():
    """Create user profile after registration"""
    # Check if user already has a profile
    if current_user.profile:
        return redirect(url_for('profile.view_profile'))
    
    # Get email from session if available (from registration)
    pending_email = session.pop('pending_email', None)

    if request.method == 'POST':
        # Get form data
        profile_name = request.form.get('profile_name', '').strip()
        profession = request.form.get('profession', '').strip()
        institution = request.form.get('institution', '').strip()
        date_of_birth_str = request.form.get('date_of_birth', '').strip()
        email = request.form.get('email', '').strip()
        grade = request.form.get('grade', '').strip()

        # Validate required fields
        if not all([profile_name, profession, institution, date_of_birth_str]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('profile_create.html', pending_email=pending_email)

        try:
            # Parse date of birth
            date_of_birth = datetime.strptime(
                date_of_birth_str, '%Y-%m-%d').date()

            # Handle file upload
            picture_filename = None
            if 'picture' in request.files:
                file = request.files['picture']
                if file and file.filename and allowed_file(file.filename):
                    ensure_upload_folder()
                    # Create unique filename with timestamp
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    picture_filename = f"{current_user.id}_{timestamp}_{filename}"
                    file.save(os.path.join(UPLOAD_FOLDER, picture_filename))

            # Create profile
            new_profile = Profile(
                user_id=current_user.id,
                profile_name=profile_name,
                picture_filename=picture_filename,
                email=email if email else None,
                profession=profession,
                institution=institution,
                date_of_birth=date_of_birth,
                grade=grade if grade else None
            )

            db.session.add(new_profile)
            db.session.commit()

            flash('Profile created successfully!', 'success')
            return redirect(url_for('dashboard.dashboard'))

        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating profile: {str(e)}', 'danger')

    return render_template('profile_create.html', pending_email=pending_email)


@profile_bp.route('/profile')
@login_required
def view_profile():
    """View user profile"""
    if not current_user.profile:
        flash('Please create your profile first.', 'info')
        return redirect(url_for('profile.create_profile'))

    return render_template('profile_view.html', profile=current_user.profile)


@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if not current_user.profile:
        return redirect(url_for('profile.create_profile'))

    profile = current_user.profile

    if request.method == 'POST':
        # Get form data
        profile_name = request.form.get('profile_name', '').strip()
        profession = request.form.get('profession', '').strip()
        institution = request.form.get('institution', '').strip()
        date_of_birth_str = request.form.get('date_of_birth', '').strip()
        email = request.form.get('email', '').strip()
        grade = request.form.get('grade', '').strip()

        # Validate required fields
        if not all([profile_name, profession, institution, date_of_birth_str]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('profile_edit.html', profile=profile)

        try:
            # Parse date of birth
            date_of_birth = datetime.strptime(
                date_of_birth_str, '%Y-%m-%d').date()

            # Handle file upload
            if 'picture' in request.files:
                file = request.files['picture']
                if file and file.filename and allowed_file(file.filename):
                    ensure_upload_folder()
                    # Delete old picture if exists
                    if profile.picture_filename:
                        old_path = os.path.join(
                            UPLOAD_FOLDER, profile.picture_filename)
                        if os.path.exists(old_path):
                            os.remove(old_path)

                    # Save new picture
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    picture_filename = f"{current_user.id}_{timestamp}_{filename}"
                    file.save(os.path.join(UPLOAD_FOLDER, picture_filename))
                    profile.picture_filename = picture_filename

            # Update profile
            profile.profile_name = profile_name
            profile.profession = profession
            profile.email = email if email else None
            profile.institution = institution
            profile.date_of_birth = date_of_birth
            profile.grade = grade if grade else None

            db.session.commit()

            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile.view_profile'))

        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')

    return render_template('profile_edit.html', profile=profile)


@profile_bp.route('/download-expenses-csv')
@login_required
def download_expenses_csv():
    """Export user's expense history as CSV."""
    try:
        # Get all expenses for current user, ordered by date descending
        expenses = Expense.query.filter_by(user_id=current_user.id).order_by(
            Expense.date.desc()).all()

        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(['Date', 'Created At', 'Name', 'Category', 'Type',
                        'Amount (৳)', 'Description'])

        # Write expense rows
        for expense in expenses:
            writer.writerow([
                expense.date.strftime('%Y-%m-%d    ') if expense.date else 'N/A',
                expense.created_at.strftime(
                    '%H:%M:%S    ') if expense.created_at else 'N/A',
                expense.name or '',
                expense.category or 'Other',
                expense.type or 'Personal',
                f"{expense.amount:.2f}",
                expense.description or ''
            ])

        # Add summary row
        total_amount = sum(exp.amount for exp in expenses)
        writer.writerow([])
        writer.writerow(['TOTAL', '', '', '', '', f"{total_amount:.2f}", ''])

        # Create response
        csv_content = output.getvalue()
        response = make_response(csv_content)
        response.headers[
            'Content-Disposition'] = f'attachment; filename=Expense_History_{current_user.username}_{datetime.now().strftime("%Y%m%d")}.csv'
        response.headers['Content-Type'] = 'text/csv'

        return response

    except Exception as e:
        flash(f'Error exporting expenses: {str(e)}', 'danger')
        return redirect(url_for('profile.view_profile'))


@profile_bp.route('/profile/delete', methods=['POST'])
@login_required
def delete_profile():
    """Delete entire user account with all associated data"""
    try:
        # Verify password
        password = request.form.get('password', '')
        if not password:
            flash('Password is required to delete your account.', 'danger')
            return redirect(url_for('profile.view_profile'))

        if not check_password_hash(current_user.password_hash, password):
            flash('Incorrect password. Account deletion cancelled.', 'danger')
            return redirect(url_for('profile.view_profile'))

        user = current_user
        user_id = user.id

        # Delete profile picture if exists
        if user.profile and user.profile.picture_filename:
            picture_path = os.path.join(
                UPLOAD_FOLDER, user.profile.picture_filename)
            if os.path.exists(picture_path):
                os.remove(picture_path)

        # Delete all user-related data
        # 1. Delete profile
        if user.profile:
            db.session.delete(user.profile)

        # 2. Delete personal expenses
        Expense.query.filter_by(user_id=user_id).delete()

        # 3. Delete debts where user is involved
        Debt.query.filter_by(user_id=user_id).delete()

        # 4. Delete group expense splits
        ExpenseSplit.query.filter_by(user_id=user_id).delete()

        # 5. Delete group expenses paid by user
        GroupExpense.query.filter_by(paid_by=user_id).delete()

        # 6. Remove user from all groups
        GroupMember.query.filter_by(user_id=user_id).delete()

        # 7. Finally, delete the user account
        db.session.delete(user)
        db.session.commit()

        # Logout the user
        logout_user()

        flash('Your account has been permanently deleted.', 'success')
        return redirect(url_for('auth.login'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting account: {str(e)}', 'danger')
        return redirect(url_for('profile.view_profile'))
