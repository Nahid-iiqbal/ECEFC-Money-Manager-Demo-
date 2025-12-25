from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from routes.database import db, Profile
from werkzeug.utils import secure_filename
from datetime import datetime
import os

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
    
    if request.method == 'POST':
        # Get form data
        profile_name = request.form.get('profile_name', '').strip()
        profession = request.form.get('profession', '').strip()
        institution = request.form.get('institution', '').strip()
        date_of_birth_str = request.form.get('date_of_birth', '').strip()
        grade = request.form.get('grade', '').strip()
        
        # Validate required fields
        if not all([profile_name, profession, institution, date_of_birth_str]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('profile_create.html')
        
        try:
            # Parse date of birth
            date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
            
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
    
    return render_template('profile_create.html')

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
        grade = request.form.get('grade', '').strip()
        
        # Validate required fields
        if not all([profile_name, profession, institution, date_of_birth_str]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('profile_edit.html', profile=profile)
        
        try:
            # Parse date of birth
            date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
            
            # Handle file upload
            if 'picture' in request.files:
                file = request.files['picture']
                if file and file.filename and allowed_file(file.filename):
                    ensure_upload_folder()
                    # Delete old picture if exists
                    if profile.picture_filename:
                        old_path = os.path.join(UPLOAD_FOLDER, profile.picture_filename)
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
