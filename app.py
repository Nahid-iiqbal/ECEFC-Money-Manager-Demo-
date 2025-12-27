# Redirect root URL to landing page
from flask import Flask, render_template, session, redirect, url_for, flash, request, jsonify
import re
import os
from datetime import datetime, timezone, timedelta
from flask_mail import Mail, Message
from flask_login import LoginManager, current_user
from dotenv import load_dotenv

# Import Blueprints
from routes.profile import profile_bp
from routes.tuition import tuition_bp
from routes.group import group
from routes.dashboard import dashboard_bp
from routes.expense import expense
from routes.auth import auth_bp
from routes.database import db, User

# Check if running on Vercel
IS_VERCEL = os.environ.get('VERCEL_DEPLOYMENT') == 'true'

# Load environment variables once at the start
load_dotenv()
is_loaded = load_dotenv()
print(f"Did .env load? {is_loaded}")

app = Flask(__name__)

# Check if running on Vercel
IS_VERCEL = os.environ.get('VERCEL_DEPLOYMENT') == 'true'

# Conditionally import SocketIO and APScheduler
if not IS_VERCEL:
    from flask_socketio import SocketIO, emit, join_room, leave_room
    from flask_apscheduler import APScheduler
else:
    # Dummy classes for Vercel
    SocketIO = None
    APScheduler = None
    emit = None
    join_room = None
    leave_room = None

# --- GROQ AI SETUP ---
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
if GROQ_API_KEY:
    print(f"Key found! Starts with: {GROQ_API_KEY[:4]}...")
else:
    print("Key NOT found.")
GROQ_MODEL_NAME = os.environ.get('GROQ_MODEL_NAME', 'mixtral-8x7b-32768')
groq_client = None

try:
    from groq import Groq
    import httpx
except ImportError:
    Groq = None


if Groq and GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        print(f"✅ Groq initialized with model: {GROQ_MODEL_NAME}")
    except Exception as e:
        print(f"❌ Groq initialization failed: {e}")
else:
    print("⚠️ Groq API Key missing. AI features disabled.")


# --- APP CONFIGURATION ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_DURATION'] = 86400  # 1 day in seconds

# Initialize database
db.init_app(app)

# Create tables
try:
    with app.app_context():
        db.create_all()
        print("✅ Database tables checked/created")
except Exception as e:
    print(f"⚠️ Database initialization note: {e}")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Add cache control headers
@app.after_request
def add_security_headers(response):
    if request.endpoint and request.endpoint not in ['static', 'home', 'auth.login', 'auth.register']:
        if current_user.is_authenticated:
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
    return response

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(expense)
app.register_blueprint(dashboard_bp)
app.register_blueprint(group)
app.register_blueprint(tuition_bp)
app.register_blueprint(profile_bp)

# --- MAIL CONFIGURATION ---
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER') or os.environ.get('MAIL_USERNAME', 'noreply@FinBuddy.com')

mail = Mail(app)

# Initialize SocketIO and Scheduler
if not IS_VERCEL:
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
else:
    socketio = None
    scheduler = None

# --- HELPER FUNCTIONS ---

def _username_maybe_email(username: str) -> bool:
    return isinstance(username, str) and '@' in username and '.' in username

def _week_range():
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=7)
    return start, today

def _render_email(template_path: str, **context) -> str:
    """Lightweight placeholder replacement for email templates."""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            html = f.read()
        for key, value in context.items():
            html = html.replace(f'{{{{ {key} }}}}', str(value))
        return html
    except FileNotFoundError:
        print(f"Error: Template {template_path} not found.")
        return ""

def _parse_time_str(value: str):
    if not value:
        return None
    for fmt in ('%H:%M', '%I:%M %p'):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue
    return None

# --- EMAIL LOGIC ---

def send_reminder_email(expense_id):
    from routes.database import Expense, User
    with app.app_context():
        expense = Expense.query.get(expense_id)
        if not expense or expense.reminder_sent:
            return

        user = User.query.get(expense.user_id)
        if not user or not user.profile or not user.profile.email:
            return

        try:
            msg = Message(
                subject=f'Reminder: {expense.category} - {expense.name}',
                recipients=[user.profile.email],
                html=f"Reminder for expense: {expense.name} - {expense.amount}" # Simplified for safety
            )
            mail.send(msg)
            expense.reminder_sent = True
            db.session.commit()
        except Exception as e:
            print(f'Error sending reminder email: {str(e)}')

def schedule_reminder_email(expense_id, reminder_datetime):
    if not scheduler: return
    try:
        scheduler.add_job(
            func=send_reminder_email,
            trigger='date',
            run_date=reminder_datetime,
            args=[expense_id],
            id=f'reminder_{expense_id}',
            replace_existing=True
        )
    except Exception as e:
        print(f'Error scheduling reminder: {str(e)}')

if scheduler:
    @scheduler.task('interval', id='check_reminders', minutes=15)
    def check_and_send_reminders():
        from routes.database import Expense
        with scheduler.app.app_context():
            now = datetime.now(timezone.utc)
            due_expenses = Expense.query.filter(
                Expense.reminder_at <= now,
                Expense.reminder_sent == False,
                Expense.reminder_at.isnot(None)
            ).all()
            for expense in due_expenses:
                send_reminder_email(expense.id)

def _build_weekly_report_html(user_id: int):
    from routes.database import Expense
    start_date, end_date = _week_range()
    
    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.date >= start_date,
        Expense.date <= end_date,
    ).order_by(Expense.created_at.desc()).all()

    total = sum((e.amount or 0) for e in expenses)
    
    # Simple table generation
    if expenses:
        transaction_rows = "".join([f"<p>{e.name}: {e.amount}</p>" for e in expenses[:5]])
    else:
        transaction_rows = "<p>No expenses.</p>"

    html = _render_email(
        'templates/email_weekly_report.html',
        start_date=start_date,
        end_date=end_date,
        total=f"{total:,.2f}",
        transaction_rows=transaction_rows,
        category_rows="", 
        no_expenses_message=""
    )
    subject = f"FinBuddy Weekly Report ({start_date} - {end_date})"
    return subject, html

def send_weekly_reports():
    from routes.database import User
    test_override = os.environ.get('REPORT_TEST_EMAIL')
    with app.app_context():
        users = User.query.all()
        for user in users:
            recipient = None
            if getattr(user, 'profile', None) and getattr(user.profile, 'email', None):
                recipient = user.profile.email
            elif _username_maybe_email(user.username):
                recipient = user.username
            elif test_override:
                recipient = test_override

            if not recipient: continue

            subject, html = _build_weekly_report_html(user.id)
            try:
                msg = Message(subject=subject, recipients=[recipient], html=html)
                mail.send(msg)
            except Exception as e:
                print(f"Failed to send weekly report: {e}")

if scheduler and os.environ.get('ENABLE_WEEKLY_REPORTS', 'true').lower() == 'true':
    day = os.environ.get('WEEKLY_REPORT_DAY', 'sun')
    hour = int(os.environ.get('WEEKLY_REPORT_HOUR', '8'))
    scheduler.add_job(id='weekly_reports', func=send_weekly_reports, trigger='cron',
                      day_of_week=day, hour=hour, minute=0, replace_existing=True)

def send_tuition_email_reminders():
    # Logic for tuition reminders
    pass 

if scheduler and os.environ.get('ENABLE_TUITION_REMINDERS', 'true').lower() == 'true':
    scheduler.add_job(id='tuition_email_reminders', func=send_tuition_email_reminders,
                      trigger='interval', minutes=1, replace_existing=True)

# --- ROUTES ---

@app.route('/')
def home():
    """Show landing page for public, redirect to dashboard if authenticated."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    return render_template('landing.html')

@app.route('/landing')
def landing():
    return render_template('landing.html')

@app.route('/r/w')
def send_weekly_now():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    recipient = None
    if getattr(current_user, 'profile', None) and getattr(current_user.profile, 'email', None):
        recipient = current_user.profile.email
    elif _username_maybe_email(current_user.username):
        recipient = current_user.username
    else:
        recipient = os.environ.get('MAIL_DEFAULT_SENDER')
        
    if not recipient:
        flash('No recipient email found.', 'error')
        return redirect(url_for('dashboard.dashboard'))
        
    subject, html = _build_weekly_report_html(current_user.id)
    try:
        msg = Message(subject=subject, recipients=[recipient], html=html)
        mail.send(msg)
        flash('Weekly report sent.', 'success')
    except Exception as e:
        flash(f'Failed to send email: {e}', 'error')
    return redirect(url_for('dashboard.dashboard'))

@app.route('/r/t')
def send_tuition_reminders_now():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    # Logic to send immediate tuition reminder
    flash('Tuition reminder check triggered.', 'info')
    return redirect(url_for('tuition.tuition_list'))

@app.route('/api/chatbot', methods=['POST'])
def ai_chatbot():
    """AI responder with full user context."""
    if not current_user.is_authenticated:
        return jsonify({'error': 'unauthorized'}), 401

    payload = request.get_json(silent=True) or {}
    user_message = (payload.get('message') or '').strip()

    # Import snapshot builder (Ensure these files exist in your project)
    try:
        from services.chat_context import build_user_finance_snapshot, get_display_name
        from routes.database import Expense, TuitionRecord, GroupMember
    except ImportError:
        return jsonify({'reply': "Error: Chat services module missing on server."})

    display_name = get_display_name(current_user)
    snapshot = build_user_finance_snapshot(current_user.id, db.session, days=60)

    # Gather Context
    profile = getattr(current_user, 'profile', None)
    profession = getattr(profile, 'profession', None) or 'not set'
    institution = getattr(profile, 'institution', None) or 'not set'

    # Stats
    week_ago = datetime.now(timezone.utc).date() - timedelta(days=7)
    recent_expenses = Expense.query.filter(Expense.user_id == current_user.id, Expense.date >= week_ago).all()
    total_recent = sum((e.amount or 0) for e in recent_expenses)
    
    all_expenses = Expense.query.filter(Expense.user_id == current_user.id).all()
    total_all_time = sum((e.amount or 0) for e in all_expenses)

    # Tuition Stats
    tuition_records = TuitionRecord.query.filter(TuitionRecord.user_id == current_user.id).all()
    total_tuition_income = sum((t.amount or 0) for t in tuition_records)
    active_students = len(tuition_records)
    
    group_count = GroupMember.query.filter(GroupMember.user_id == current_user.id).count()

    ai_user_message = user_message or "Give me a friendly summary of my status."

    if not groq_client:
        return jsonify({'reply': "AI is currently unavailable. Check server logs for API Key or Library issues."})

    system_prompt = f"""
You are FeinBuddy, a warm, intelligent personal finance assistant. 

### USER PROFILE
- **Name:** {display_name}
- **Profession:** {profession}
- **Institution:** {institution}

### FINANCIAL SNAPSHOT
- **Recent Spending (7 Days):** ৳{total_recent:,.2f}
- **All-Time Spending:** ৳{total_all_time:,.2f}
- **Tuition Income Potential:** ৳{total_tuition_income:,.2f} ({active_students} students)
- **Active Groups:** {group_count}

### HISTORY
{snapshot}

### INSTRUCTIONS
1. Be friendly and polite. Use emojis (💰, 📊).
2. **MUST** use Markdown formatting.
3. Strictly answer finance/app questions only.
4. Keep it short (under 300 words).
    """

    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": ai_user_message}
            ],
            temperature=0.6,
            max_tokens=800
        )
        reply = (completion.choices[0].message.content or '').strip()
        return jsonify({'reply': reply})
    except Exception as e:
        print(f"Groq API Error: {e}")
        return jsonify({'reply': "I'm having trouble accessing my brain right now. 🧠"})

# --- PREFERENCES TOGGLES ---

@app.route('/toggle-email-notifications', methods=['POST'])
def toggle_email_notifications():
    if not current_user.is_authenticated: return jsonify({'success': False}), 401
    try:
        data = request.get_json()
        current_user.email_notifications = data.get('enabled', False)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Updated'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/toggle-weekly-expense-report', methods=['POST'])
def toggle_weekly_expense_report():
    if not current_user.is_authenticated: return jsonify({'success': False}), 401
    try:
        data = request.get_json()
        current_user.weekly_expense_report = data.get('enabled', False)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Updated'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/toggle-tuition-reminder', methods=['POST'])
def toggle_tuition_reminder():
    if not current_user.is_authenticated: return jsonify({'success': False}), 401
    try:
        data = request.get_json()
        current_user.tuition_reminder = data.get('enabled', False)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Updated'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# --- SOCKET IO ---
if not IS_VERCEL and socketio:
    @socketio.on('connect')
    def handle_connect():
        if current_user.is_authenticated:
            join_room(f'user_{current_user.id}')

    @socketio.on('request_dashboard_update')
    def handle_dashboard_update(data):
        if not current_user.is_authenticated: return
        try:
            from routes.dashboard import get_dashboard_data
            emit('dashboard_updated', get_dashboard_data(), to=f'user_{current_user.id}')
        except Exception as e:
            print(f"Socket Error: {e}")

# --- MAIN ---
if __name__ == '__main__':
    print("=" * 50)
    print("FinBuddy - Starting Application")
    print("=" * 50)
    
    if IS_VERCEL:
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)