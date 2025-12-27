# In routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, Email
from routes.database import db, User, Profile
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from sqlalchemy.exc import IntegrityError

auth_bp = Blueprint('auth', __name__)


class LoginForm(FlaskForm):
    username = StringField(render_kw={"placeholder": "Username"}, validators=[
                           InputRequired(), Length(min=4, max=15)])
    password = PasswordField(render_kw={"placeholder": "Password"}, validators=[
                             InputRequired(), Length(min=8, max=80)])
    submit = SubmitField('Login')


class RegisterForm(FlaskForm):
    username = StringField(render_kw={"placeholder": "Username"}, validators=[
                           InputRequired(), Length(min=4, max=15)])
    email = StringField(render_kw={"placeholder": "Email"}, validators=[
                       InputRequired(), Email(message='Invalid email address')])
    password = PasswordField(render_kw={"placeholder": "Password"}, validators=[
                             InputRequired(), Length(min=8, max=80)])
    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user = User.query.filter_by(username=username.data).first()
        if existing_user:
            raise ValidationError(
                'Username already exists. Please choose a different one.')
    
    def validate_email(self, email):
        # Check if email exists in Profile table
        existing_profile = Profile.query.filter_by(email=email.data).first()
        if existing_profile:
            raise ValidationError(
                'Email already registered. Please use a different email.')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Login logic
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=True)
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    # Prevent caching of login page
    response = make_response(render_template('auth_new.html', form=form, mode='login'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Register logic
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            hashed_password = generate_password_hash(form.password.data)
            new_user = User(username=form.username.data,
                            password_hash=hashed_password)
            db.session.add(new_user)
            db.session.flush()  # Get user ID without committing
            
            # Store email in session for profile creation
            session['pending_email'] = form.email.data
            
            db.session.commit()
            login_user(new_user, remember=True)
            flash(f'Welcome, {new_user.username}!', 'success')
            return redirect(url_for('profile.onboarding_profile'))
        except IntegrityError:
            db.session.rollback()
            flash('Username already exists. Please choose a different one.', 'danger')
    
    # Prevent caching of register page
    response = make_response(render_template('auth_new.html', form=form, mode='register'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@auth_bp.route('/logout')
def logout():
    """Handle user logout."""
    logout_user()
    session.clear()
    flash('You have been logged out successfully.', 'info')
    
    # Create response with cache prevention
    response = make_response(redirect(url_for('auth.login')))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
