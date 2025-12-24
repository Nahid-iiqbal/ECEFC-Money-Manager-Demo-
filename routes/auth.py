# In routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Login logic
    return render_template('auth.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Register logic
    return render_template('auth.html')


@auth_bp.route('/logout')
def logout():
    # Logout logic
    return redirect(url_for('home'))
