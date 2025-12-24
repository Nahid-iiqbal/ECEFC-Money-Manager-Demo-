from flask import Flask, render_template, session, redirect, url_for
import os
from dotenv import load_dotenv
import database
from routes import register_blueprints

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', 'sqlite:///finance.db')

# Initialize database
database.init_db()

# Register all blueprints
register_blueprints(app)


@app.route('/')
def index():
    """Home page route."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session.get('user_id')
    username = session.get('username')
    
    # Get quick stats
    conn = database.get_db_connection()
    
    # Personal expenses count
    personal_count = conn.execute(
        'SELECT COUNT(*) as count FROM personal_expenses WHERE user_id = ?',
        (user_id,)
    ).fetchone()['count']
    
    # Personal total
    personal_total = conn.execute(
        'SELECT SUM(amount) as total FROM personal_expenses WHERE user_id = ?',
        (user_id,)
    ).fetchone()['total'] or 0
    
    # Groups count
    groups_count = conn.execute(
        'SELECT COUNT(*) as count FROM group_members WHERE user_id = ?',
        (user_id,)
    ).fetchone()['count']
    
    # Tuition records count
    tuition_count = conn.execute(
        'SELECT COUNT(*) as count FROM tuition_records WHERE user_id = ?',
        (user_id,)
    ).fetchone()['count']
    
    # Tuition total due
    tuition_due = conn.execute(
        'SELECT SUM(amount - paid_amount) as due FROM tuition_records WHERE user_id = ?',
        (user_id,)
    ).fetchone()['due'] or 0
    
    conn.close()
    
    return render_template(
        'index.html',
        username=username,
        personal_count=personal_count,
        personal_total=personal_total,
        groups_count=groups_count,
        tuition_count=tuition_count,
        tuition_due=tuition_due
    )


@app.route('/about')
def about():
    """About page route."""
    return render_template('index.html', mode='about')


@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('index.html', error='Page not found'), 404


@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors."""
    return render_template('index.html', error='Internal server error'), 500


# Context processor to make session available in all templates
@app.context_processor
def inject_user():
    """Inject user info into all templates."""
    return {
        'logged_in': 'user_id' in session,
        'username': session.get('username', '')
    }


if __name__ == '__main__':
    # Run the application
    print("=" * 50)
    print("FeinBuddy - Starting Application")
    print("=" * 50)
    print(f"Database: {app.config['DATABASE_URL']}")
    print("Server starting on http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
