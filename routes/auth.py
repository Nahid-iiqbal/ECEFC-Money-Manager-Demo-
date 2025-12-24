# In routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from routes.database import db, User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required

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
    password = PasswordField(render_kw={"placeholder": "Password"}, validators=[
                             InputRequired(), Length(min=8, max=80)])
    submit = SubmitField('Register')


def validate_username(self, username):
    existing_user = User.query.filter_by(username=username.data).first()
    if existing_user:
        raise ValidationError(
            'Username already exists. Please choose a different one.')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Login logic
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('auth.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Register logic
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data,
                        password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)


@auth_bp.route('/logout')
def logout():
    """Handle user logout."""
    logout_user()
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
