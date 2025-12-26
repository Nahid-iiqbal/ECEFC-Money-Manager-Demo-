from flask import Flask, render_template, session, redirect, url_for, flash, request, jsonify
from dotenv import load_dotenv
from routes.database import db, User
from routes.auth import auth_bp
from routes.expense import expense
from routes.dashboard import dashboard_bp
from routes.group import group
from routes.tuition import tuition_bp
from routes.profile import profile_bp
from flask_login import LoginManager, current_user
from flask_apscheduler import APScheduler
from flask_mail import Mail, Message
import os

try:
    from groq import Groq
except ImportError:
    Groq = None

load_dotenv()
app = Flask(__name__)

GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
GROQ_MODEL_NAME = os.environ.get('GROQ_MODEL_NAME', 'mixtral-8x7b-32768')
groq_client = None

if Groq and GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        print(f"Groq initialized with model: {GROQ_MODEL_NAME}")
    except Exception as e:
        print(f"Groq setup failed: {e}")

# Configuration
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_DURATION'] = 86400  # 1 day in seconds

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
app.register_blueprint(group)
app.register_blueprint(tuition_bp)

app.register_blueprint(profile_bp)
# Mail configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.environ.get(
    'MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.environ.get(
    'MAIL_USE_SSL', 'false').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get(
    'MAIL_DEFAULT_SENDER') or os.environ.get('MAIL_USERNAME', 'noreply@feinbuddy.com')

mail = Mail(app)

# Scheduler setup
scheduler = APScheduler()
scheduler.init_app(app)


def _username_maybe_email(username: str) -> bool:
    return isinstance(username, str) and '@' in username and '.' in username


def _week_range():
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    start = today - timedelta(days=7)
    return start, today


def _render_email(template_path: str, **context) -> str:
    """Lightweight placeholder replacement for email templates."""
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()
    for key, value in context.items():
        html = html.replace(f'{{{{ {key} }}}}', str(value))
    return html


def _build_weekly_report_html(user_id: int):
    from datetime import datetime
    from routes.database import Expense
    from flask import render_template_string
    start_date, end_date = _week_range()

    # Query expenses for last 7 days, ordered by date and time
    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.date >= start_date,
        Expense.date <= end_date,
    ).order_by(Expense.created_at.desc()).all()

    total = sum((e.amount or 0) for e in expenses)

    # Aggregate by category with count
    by_cat = {}
    for e in expenses:
        key = (e.category or 'Other')
        if key not in by_cat:
            by_cat[key] = {'amount': 0, 'count': 0}
        by_cat[key]['amount'] += (e.amount or 0)
        by_cat[key]['count'] += 1

    # Build category rows with count
    if by_cat:
        category_rows = ''.join(
            f"<tr><td style='padding:12px;border-bottom:1px solid #273245;color:#f1f5f9;font-weight:700'>{c}</td>"
            f"<td style='padding:12px;border-bottom:1px solid #273245;text-align:right;color:#f8fafc;font-weight:800'>৳{v['amount']:,.2f}</td>"
            f"<td style='padding:12px;border-bottom:1px solid #273245;text-align:right;color:#cbd5e1;font-weight:700'>{v['count']}</td></tr>"
            for c, v in sorted(by_cat.items(), key=lambda x: -x[1]['amount'])
        )
    else:
        category_rows = "<tr><td colspan='3' style='padding:12px;color:#6c757d;text-align:center'>No expenses this week</td></tr>"

    # Build transaction rows with time
    if expenses:
        transaction_rows = ''
        for e in expenses[:10]:  # Show latest 10 transactions
            time_str = e.created_at.strftime(
                '%b %d, %I:%M %p') if e.created_at else e.date.strftime('%b %d')
            transaction_rows += f"""
                <div style='padding:12px;border-bottom:1px solid #273245;display:flex;justify-content:space-between;align-items:center'>
                    <div>
                        <p style='margin:0;color:#f8fafc;font-weight:800;font-size:14px'>{e.name}</p>
                        <p style='margin:4px 0 0;color:#cbd5e1;font-size:12px;font-weight:700'>{time_str} • {e.category or 'Other'}</p>
                    </div>
                    <div style='text-align:right'>
                        <p style='margin:0;color:#fca5a5;font-weight:900;font-size:16px'>৳{e.amount:,.2f}</p>
                    </div>
                </div>
            """
        no_expenses_message = ''
    else:
        transaction_rows = "<p style='text-align:center;color:#cbd5e1;padding:20px;margin:0;font-weight:700'>No transactions recorded this week.</p>"
        no_expenses_message = ""

    html = _render_email(
        'templates/email_weekly_report.html',
        start_date=start_date,
        end_date=end_date,
        total=f"{total:,.2f}",
        category_rows=category_rows,
        transaction_rows=transaction_rows,
        no_expenses_message=no_expenses_message,
    )

    subject = f"FeinBuddy Weekly Report ({start_date} - {end_date})"
    return subject, html


def send_weekly_reports():
    # Iterate all users and email where possible
    from routes.database import User
    test_override = os.environ.get('REPORT_TEST_EMAIL')
    with app.app_context():
        users = User.query.all()
        for user in users:
            recipient = None
            # Prefer profile email if present
            if getattr(user, 'profile', None) and getattr(user.profile, 'email', None):
                recipient = user.profile.email
            elif _username_maybe_email(user.username):
                recipient = user.username
            elif test_override:
                recipient = test_override

            if not recipient:
                continue

            subject, html = _build_weekly_report_html(user.id)
            try:
                msg = Message(subject=subject, recipients=[
                              recipient], html=html)
                mail.send(msg)
            except Exception as e:
                print(f"Failed to send weekly report to {recipient}: {e}")


if os.environ.get('ENABLE_WEEKLY_REPORTS', 'true').lower() == 'true':
    # Default: every Sunday at 08:00 server time
    day = os.environ.get('WEEKLY_REPORT_DAY', 'sun')
    hour = int(os.environ.get('WEEKLY_REPORT_HOUR', '8'))
    scheduler.add_job(id='weekly_reports', func=send_weekly_reports, trigger='cron',
                      day_of_week=day, hour=hour, minute=0, replace_existing=True)
    if not scheduler.running:
        scheduler.start()


# Tuition email reminders (2h and 1h before class time)
def _parse_time_str(value: str):
    if not value:
        return None
    from datetime import datetime
    for fmt in ('%H:%M', '%I:%M %p'):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue
    return None


def send_tuition_email_reminders():
    from datetime import datetime, timedelta
    from routes.database import TuitionRecord, User

    now = datetime.now()
    # Sunday=0 mapping used in app
    today_idx = (now.weekday() + 1) % 7

    with app.app_context():
        records = TuitionRecord.query.filter(
            TuitionRecord.tuition_time.isnot(None)
        ).all()

        for record in records:
            if record.days and today_idx not in (record.days or []):
                continue

            class_time = _parse_time_str(record.tuition_time)
            if not class_time:
                continue

            class_dt = datetime.combine(now.date(), class_time)
            if class_dt <= now:
                continue

            user = db.session.get(User, record.user_id)
            # Determine recipient
            if getattr(user, 'profile', None) and getattr(user.profile, 'email', None):
                recipient = user.profile.email
            elif _username_maybe_email(user.username):
                recipient = user.username
            else:
                recipient = os.environ.get('REPORT_TEST_EMAIL')
            if not recipient:
                continue

            for offset_hours in (2, 1):
                target_dt = class_dt - timedelta(hours=offset_hours)
                delta = (now - target_dt).total_seconds()
                if 0 <= delta < 60:
                    subject = f"Reminder: Tuition in {offset_hours} hour{'s' if offset_hours > 1 else ''}"
                    at_time = class_dt.strftime('%I:%M %p')

                    # Load template and render
                    with open('templates/email_tuition_reminder.html', 'r', encoding='utf-8') as f:
                        html = f.read()

                    html = html.replace(
                        '{{ reminder_time }}', f"Class in {offset_hours} hour{'s' if offset_hours > 1 else ''}")
                    html = html.replace(
                        '{{ hours_remaining }}', f"{offset_hours} hour{'s' if offset_hours > 1 else ''}")
                    html = html.replace(
                        '{{ student_name }}', record.student_name)
                    html = html.replace('{{ class_time }}', at_time)
                    html = html.replace('{{ address }}', record.address)
                    per_class = (record.amount / record.total_days) if getattr(
                        record, 'total_days', 0) else record.amount
                    html = html.replace('{{ amount }}', f"{per_class:,.2f}")

                    try:
                        msg = Message(subject=subject, recipients=[
                                      recipient], html=html)
                        mail.send(msg)
                    except Exception as e:
                        print(
                            f"Failed to send tuition reminder to {recipient}: {e}")


if os.environ.get('ENABLE_TUITION_REMINDERS', 'true').lower() == 'true':
    # Run every minute to catch reminder thresholds
    scheduler.add_job(id='tuition_email_reminders', func=send_tuition_email_reminders,
                      trigger='interval', minutes=1, replace_existing=True)
    if not scheduler.running:
        scheduler.start()


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
        flash('No recipient email found. Add REPORT_TEST_EMAIL env or use an email username.', 'error')
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

    from datetime import datetime
    from routes.database import TuitionRecord, User

    now = datetime.now()
    today_idx = (now.weekday() + 1) % 7

    # Determine recipient for current user
    user = db.session.get(User, current_user.id)
    if getattr(user, 'profile', None) and getattr(user.profile, 'email', None):
        recipient = user.profile.email
    elif _username_maybe_email(user.username):
        recipient = user.username
    else:
        recipient = os.environ.get('REPORT_TEST_EMAIL')
    if not recipient:
        flash('No recipient email found. Add email in Profile or set REPORT_TEST_EMAIL.', 'error')
        return redirect(url_for('tuition.tuition_list'))

    # Find next upcoming class today for this user
    records = TuitionRecord.query.filter(
        TuitionRecord.user_id == current_user.id,
        TuitionRecord.tuition_time.isnot(None)
    ).all()

    candidates = []
    for record in records:
        if record.days and today_idx not in (record.days or []):
            continue
        t = _parse_time_str(record.tuition_time)
        if not t:
            continue
        class_dt = datetime.combine(now.date(), t)
        if class_dt > now:
            candidates.append((class_dt, record))

    if not candidates:
        flash('No upcoming tuition found for today.', 'info')
        return redirect(url_for('tuition.tuition_list'))

    class_dt, record = sorted(candidates, key=lambda x: x[0])[0]
    at_time = class_dt.strftime('%I:%M %p')
    subject = f"Reminder: Tuition Today at {at_time}"

    # Calculate time until class
    time_diff = class_dt - now
    hours_until = time_diff.total_seconds() / 3600
    if hours_until < 1:
        time_remaining = f"{int(time_diff.total_seconds() / 60)} minutes"
    else:
        time_remaining = f"{int(hours_until)} hour{'s' if int(hours_until) > 1 else ''}"

    # Load template and render
    per_class = (record.amount / record.total_days) if getattr(record,
                                                               'total_days', 0) else record.amount
    html = _render_email(
        'templates/email_tuition_reminder.html',
        reminder_time="Class starting soon",
        hours_remaining=time_remaining,
        student_name=record.student_name,
        class_time=at_time,
        address=record.address,
        amount=f"{per_class:,.2f}",
    )

    try:
        msg = Message(subject=subject, recipients=[recipient], html=html)
        mail.send(msg)
        flash('Tuition reminder email sent.', 'success')
    except Exception as e:
        flash(f'Failed to send tuition reminder: {e}', 'error')
    return redirect(url_for('tuition.tuition_list'))


@app.route('/api/chatbot', methods=['POST'])
def ai_chatbot():
    """AI responder with full user context from database."""
    if not current_user.is_authenticated:
        return jsonify({'error': 'unauthorized'}), 401

    payload = request.get_json(silent=True) or {}
    user_message = (payload.get('message') or '').strip()

    # Gather user information from database
    from routes.database import Expense, TuitionRecord, GroupMember
    from datetime import datetime, timedelta

    profile = getattr(current_user, 'profile', None)
    display_name = getattr(profile, 'profile_name',
                           None) or current_user.username
    email = getattr(profile, 'email', None) or 'not set'
    profession = getattr(profile, 'profession', None) or 'not set'
    institution = getattr(profile, 'institution', None) or 'not set'

    # Recent expenses (last 7 days)
    week_ago = datetime.utcnow().date() - timedelta(days=7)
    recent_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= week_ago
    ).all()
    total_recent = sum((e.amount or 0) for e in recent_expenses)

    # Total spending all time
    all_expenses = Expense.query.filter(
        Expense.user_id == current_user.id).all()
    total_all_time = sum((e.amount or 0) for e in all_expenses)

    # Expense categories breakdown (last 7 days)
    category_summary = {}
    for e in recent_expenses:
        cat = e.category or 'Other'
        category_summary[cat] = category_summary.get(cat, 0) + (e.amount or 0)

    # Tuition info (income earned once 100% complete)
    tuition_records = TuitionRecord.query.filter(
        TuitionRecord.user_id == current_user.id).all()
    tuition_count = len(tuition_records) if tuition_records else 0
    total_tuition_income = sum((t.amount or 0)
                               for t in tuition_records) if tuition_records else 0

    # Calculate progress for tuition
    tuition_progress = 0
    if tuition_records:
        total_classes = sum((t.total_days or 0) for t in tuition_records)
        total_completed = sum((t.total_completed or 0)
                              for t in tuition_records)
        if total_classes > 0:
            tuition_progress = int((total_completed / total_classes) * 100)

    # Group memberships
    group_count = GroupMember.query.filter(
        GroupMember.user_id == current_user.id).count()

    # Build context summary
    category_str = ', '.join([f"{k}: ৳{v:,.0f}" for k, v in sorted(
        category_summary.items(), key=lambda x: -x[1])[:3]])

    if not user_message:
        greeting = f"Hi {display_name}! 👋 Here's your quick summary:\n"
        greeting += f"💰 This week: ৳{total_recent:,.0f} spent | All-time: ৳{total_all_time:,.0f}\n"
        if category_str:
            greeting += f"📊 Top categories: {category_str}\n"
        greeting += f"🎓 Tuition income potential: ৳{total_tuition_income:,.0f} ({tuition_progress}% progress) | Groups: {group_count}"
        return jsonify({'reply': greeting})

    if not groq_client:
        return jsonify({'error': 'Groq not configured. Set GROQ_API_KEY and restart the app.'}), 503

    # Build rich context for AI
    context = (
        f"User: {display_name} ({email})\n"
        f"Profession: {profession} | Institution: {institution}\n"
        f"📈 Finance Summary:\n"
        f"  - This week: ৳{total_recent:,.2f} ({len(recent_expenses)} expenses)\n"
        f"  - All-time total: ৳{total_all_time:,.2f}\n"
    )

    if category_str:
        context += f"  - Categories: {category_str}\n"

    context += (
        f"  - Tuition income potential: ৳{total_tuition_income:,.2f} ({tuition_progress}% progress, {tuition_count} classes)\n"
        f"  - Groups: {group_count} joined\n"
        f"Recent expenses: {', '.join([f'{e.name}(৳{e.amount:,.0f})' for e in recent_expenses[-5:]])}"
    )

    system_prompt = (
        "You are FeinBuddy, a friendly personal finance assistant. "
        f"You know the user's financial data: {context}\n\n"
        "CHAT naturally like a friend, NOT like a report. Keep it SHORT (2-3 sentences max). "
        "Use their data to give relevant, personalized insights and advice. "
        "Be conversational, supportive, and encouraging. Use 1-2 emoji if it fits. "
        "Never start with 'Hi', 'Hello', or greetings."
    )

    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=500
        )
        reply = (completion.choices[0].message.content or '').strip(
        ) or "I couldn't draft a reply just now."
        return jsonify({'reply': reply})
    except Exception as e:
        app.logger.exception("Groq call failed")
        return jsonify({'error': f'Groq error: {e}'}), 500


@app.route('/')
def home():
    """Display homepage or redirect to dashboard if logged in."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
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
