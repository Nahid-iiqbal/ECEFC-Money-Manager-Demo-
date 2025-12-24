from flask import Flask, render_template, redirect, url_for, session
import database
import routes
import os

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize database
database.init_db()

# Register all blueprints
routes.register_blueprints(app)


@app.route('/')
def home():
    """Redirect to dashboard if logged in, otherwise to login page."""
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('auth.login'))


if __name__ == '__main__':
    app.run(debug=True)
