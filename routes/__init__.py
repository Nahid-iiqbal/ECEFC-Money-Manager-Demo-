from flask import Blueprint

# Import all blueprints
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
# from routes.personal_expense import personal_bp
# from routes.group import group_bp
from routes.tuition import tuition_bp


def register_blueprints(app):
    """Register all blueprints with the Flask app."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    # app.register_blueprint(personal_bp)
    # app.register_blueprint(group_bp)
    app.register_blueprint(tuition_bp)
