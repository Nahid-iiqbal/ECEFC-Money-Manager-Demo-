from flask import Flask, render_template, session, redirect, url_for
from routes.database import db, User
from routes.auth import auth_bp
from routes import register_blueprints
from flask_login import LoginManager
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
    return User.query.get(int(user_id))


# Register all blueprints
register_blueprints(app)


@app.route('/')
def home():
    """Homepage - shows welcome page."""
    return render_template('index.html')


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
