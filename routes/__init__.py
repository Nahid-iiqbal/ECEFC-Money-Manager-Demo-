from flask import Flask

# Import all blueprints
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.group import group
from routes.tuition import tuition_bp
from routes.profile import profile_bp
from routes.expense import expense  # Previously 'expense' in your app.py

def register_blueprints(app: Flask):
    """Register all blueprints with the Flask app."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(group)
    app.register_blueprint(tuition_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(expense)