from flask import Flask, render_template, session, redirect, url_for
from routes.database import db, User
from routes.auth import auth_bp
from routes.expense import expense
from routes.dashboard import dashboard_bp
from routes.personal_expense import personal_bp
from routes.group import group_bp
from routes.tuition_app import tuition_bp
from flask_login import LoginManager, current_user
import os

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)
with app.app_context():
    db.create_all()

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(expense)
app.register_blueprint(dashboard_bp)
app.register_blueprint(personal_bp)
app.register_blueprint(group_bp)
app.register_blueprint(tuition_bp)

@app.route('/')
def home():
    """Redirect to dashboard if logged in, otherwise to login page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('auth.login'))


if __name__ == '__main__':
    # Run the application
    print("=" * 50)
    print("FeinBuddy - Starting Application")
    print("=" * 50)
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print("Server starting on http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)

    app.run(debug=True, host='0.0.0.0', port=5000)
