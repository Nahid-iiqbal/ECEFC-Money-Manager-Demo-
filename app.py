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
from flask_mail import Mail, Message
import os
import re

# Check if running on Vercel
IS_VERCEL = os.environ.get('VERCEL_DEPLOYMENT') == 'true'

# Conditionally import SocketIO and APScheduler (not needed on Vercel)
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


# =======================
# Intelligent Chatbot Fallback System
# =======================

def get_intelligent_fallback_response(user_message, user_context):
    """
    Provides intelligent, context-aware responses when AI API is unavailable.
    Uses pattern matching and FAQ-style responses to guide users.
    
    Args:
        user_message: The user's query (lowercase)
        user_context: Dict with user's profile and financial data
    
    Returns:
        String response or None if no pattern matches
    """
    msg = user_message.lower().strip()
    
    # Extract context variables
    display_name = user_context.get('display_name', 'there')
    total_recent = user_context.get('total_recent', 0)
    total_all_time = user_context.get('total_all_time', 0)
    category_str = user_context.get('category_str', '')
    tuition_income = user_context.get('tuition_income', 0)
    tuition_progress = user_context.get('tuition_progress', 0)
    group_count = user_context.get('group_count', 0)
    
    # ===== Greetings =====
    if re.search(r'\b(hi|hello|hey|greetings|good\s+(morning|afternoon|evening))\b', msg):
        return (
            f"Hi {display_name}! 👋 Welcome to FeinBuddy! I'm here to help you navigate this webapp. "
            f"You can ask me about features, how to use different sections, or what you can do here. "
            f"What would you like to know?"
        )
    
    # ===== What is this / Overview =====
    if re.search(r'\b(what\s+(is|does)|about|overview|purpose|tell\s+me\s+about)\b', msg) and \
       re.search(r'\b(this|app|webapp|website|feinbuddy|platform)\b', msg):
        return (
            f"FeinBuddy is your personal finance manager! 💰 It helps you:\n"
            f"📊 Track daily expenses by category\n"
            f"👥 Manage group expenses with friends\n"
            f"🎓 Track tuition classes and income\n"
            f"📈 View spending trends on your dashboard\n"
            f"You're currently managing ৳{total_all_time:,.0f} in total expenses!"
        )
    
    # ===== Features List =====
    if re.search(r'\b(feature|can\s+i|what\s+can|what\s+do|capabilities|options)\b', msg):
        return (
            "✨ **FeinBuddy Features**\n\n"
            "═══════════════════════════════════════\n\n"
            "💸 **EXPENSES**\n"
            "   ├─ Add with category, date, description\n"
            "   ├─ Edit or delete entries\n"
            "   ├─ Filter by date & category\n"
            "   └─ Track daily/weekly/monthly totals\n\n"
            "👥 **GROUPS**\n"
            "   ├─ Create shared expense groups\n"
            "   ├─ Add multiple members\n"
            "   ├─ Auto-split calculations\n"
            "   └─ Track who owes what\n\n"
            "🎓 **TUITION**\n"
            "   ├─ Add students with rates\n"
            "   ├─ Set weekly routine (days)\n"
            "   ├─ Mark attendance day-by-day\n"
            "   ├─ Calculate income\n"
            "   └─ Export PDF routine\n\n"
            "📊 **DASHBOARD**\n"
            "   ├─ Visual charts (pie, bar)\n"
            "   ├─ Weekly summaries\n"
            "   ├─ Category breakdown\n"
            "   └─ Recent transactions\n\n"
            "👤 **PROFILE**\n"
            "   └─ Update name, email, profession\n\n"
            "🎨 **THEMES**\n"
            "   └─ Light/dark mode toggle\n\n"
            "═══════════════════════════════════════\n\n"
            "Ask: 'How do I add expenses?' or 'Tell me about routine system'"
        )
    
    # ===== Dashboard Help =====
    if re.search(r'\b(dashboard|home|overview|summary|charts?|graphs?)\b', msg):
        return (
            "📊 **Dashboard** is your finance overview!\n\n"
            "You'll see:\n"
            "• Weekly spending summary\n"
            "• Expense breakdown by category (pie chart)\n"
            "• Recent transactions\n"
            "• Quick stats cards\n\n"
            "Navigate to Dashboard from the navbar to see your financial snapshot!"
        )
    
    # ===== Expense Tracking =====
    if re.search(r'\b(expense|add\s+expense|track|spending|record|log)\b', msg) and \
       not re.search(r'\bgroup', msg):
        return (
            "💸 **Expense Tracking** is easy!\n\n"
            "**To add an expense:**\n"
            "1. Go to 'Expenses' in the navbar\n"
            "2. Click 'Add Expense' button\n"
            "3. Fill in amount, category, date, description\n"
            "4. Submit!\n\n"
            "**Categories available:** Food, Transport, Entertainment, Shopping, Bills, Health, Education\n\n"
            f"So far you've tracked ৳{total_all_time:,.0f} across all categories!"
        )
    
    # ===== Group Management =====
    if re.search(r'\b(group|groups|split|shared|friends|owe|dues?|settle)\b', msg):
        return (
            "👥 **Group Expense Management**\n\n"
            "═══════════════════════════════════════\n\n"
            "**📝 Step-by-Step:**\n\n"
            "**1. Create Group**\n"
            "   → Groups page → 'Create New'\n"
            "   → Name it (Trip, Apartment, etc.)\n\n"
            "**2. Add Members**\n"
            "   → Enter each person's name\n"
            "   → Add/remove anytime\n\n"
            "**3. Log Shared Expenses**\n"
            "   → Click group → Add expense\n"
            "   → Enter amount & description\n"
            "   → Choose who paid\n"
            "   → Auto-splits equally\n\n"
            "**4. Track Balances**\n"
            "   → 'Who Owes What' section\n"
            "   → Clear breakdown shown\n"
            "   → Auto-calculated\n\n"
            "**5. Settle Dues**\n"
            "   → Mark payments settled\n"
            "   → Keep transaction history\n\n"
            "═══════════════════════════════════════\n\n"
            "**💡 Perfect For:**\n"
            "• Weekend trips • Shared apartments\n"
            "• Restaurant bills • Event planning\n\n"
            f"**Your Groups:** {group_count} active group(s)"
        )
    
    # ===== Tuition Management =====
    if re.search(r'\b(tuition|class|classes|teaching|student|income|attendance|routine)\b', msg):
        return (
            "🎓 **Tuition Tracker** - Complete Teaching Management\n\n"
            "═══════════════════════════════════════\n\n"
            "**📚 Core Features:**\n\n"
            "1️⃣ **Add Students/Classes**\n"
            "   • Set student name & rate per session\n"
            "   • Define total number of classes\n"
            "   • Choose specific days (Mon-Sun)\n"
            "   • Set start date\n\n"
            "2️⃣ **Track Attendance**\n"
            "   • Mark Present/Absent for each class\n"
            "   • Visual progress bars\n"
            "   • Auto-calculates completion\n\n"
            "3️⃣ **Income Calculator**\n"
            "   • Real-time: Rate × Total Classes\n"
            "   • Track completed vs remaining\n\n"
            "4️⃣ **Routine System** 📅\n"
            "   • Personalized routine per student\n"
            "   • Shows: Name, Days, Classes, Rate\n"
            "   • Day-by-day attendance tracking\n"
            "   • Visual status (✓ Present / ✗ Absent)\n"
            "   • Export as PDF with one click!\n\n"
            "═══════════════════════════════════════\n\n"
            f"**Your Status:** {tuition_progress}% complete | ৳{tuition_income:,.0f} potential\n\n"
            "**Quick Actions:**\n"
            "• Tuition page → Add New Student\n"
            "• Click student → Mark attendance\n"
            "• 'Export Routine PDF' → Download"
        )
    
    # ===== Profile/Settings =====
    if re.search(r'\b(profile|account|settings|personal|edit|update|change)\b', msg):
        return (
            "👤 **Profile** lets you manage your account!\n\n"
            "**You can:**\n"
            "• Update profile name\n"
            "• Set email address\n"
            "• Add profession & institution\n"
            "• View account details\n\n"
            "Go to 'Profile' in the navbar to make changes!"
        )
    
    # ===== Navigation Help =====
    if re.search(r'\b(navigate|navigation|where|find|go\s+to|menu|page)\b', msg):
        return (
            "🧭 **Navigation Guide:**\n\n"
            "Top navbar has these sections:\n"
            "• 🏠 Dashboard - Your finance overview\n"
            "• 💸 Expenses - Track daily spending\n"
            "• 👥 Groups - Shared expenses\n"
            "• 🎓 Tuition - Class management\n"
            "• 👤 Profile - Account settings\n"
            "• 🌙 Theme Toggle - Switch light/dark mode\n\n"
            "Click any section to jump there!"
        )
    
    # ===== Theme/Appearance =====
    if re.search(r'\b(theme|dark\s+mode|light\s+mode|appearance|color|design)\b', msg):
        return (
            "🎨 **Theme Options:**\n\n"
            "FeinBuddy supports light & dark themes!\n\n"
            "**To switch:**\n"
            "• Click the 🌙/☀️ icon in the navbar\n"
            "• Instantly toggles between light (purple) and dark (maroon) themes\n"
            "• Your preference is saved automatically\n\n"
            "Try it now for a fresh look!"
        )
    
    # ===== How to use / Getting Started =====
    if re.search(r'\b(how\s+to|getting\s+started|start|begin|tutorial|guide)\b', msg):
        return (
            "🚀 **Getting Started with FeinBuddy:**\n\n"
            "**Step 1:** Complete your profile (add name, profession)\n"
            "**Step 2:** Start tracking expenses (Expenses page)\n"
            "**Step 3:** Check your Dashboard for insights\n"
            "**Step 4:** Create groups for shared expenses (optional)\n"
            "**Step 5:** Add tuition classes if you teach (optional)\n\n"
            "Need help with a specific feature? Just ask!"
        )
    
    # ===== Data/Reports =====
    if re.search(r'\b(report|export|download|pdf|data|statistics|analytics)\b', msg):
        return (
            "📈 **Reports & Data Export**\n\n"
            "═══════════════════════════════════════\n\n"
            "**📊 Dashboard Analytics:**\n"
            "   • Pie charts (category breakdown)\n"
            "   • Bar graphs (spending trends)\n"
            "   • Weekly summary cards\n"
            "   • Real-time statistics\n\n"
            "**💸 Expense Reports:**\n"
            "   • Filterable table\n"
            "   • Sort by date/amount/category\n"
            "   • Search functionality\n"
            "   • Date range selection\n\n"
            "**📑 PDF Export (Tuition):**\n"
            "   • Professional routine format\n"
            "   • Student details & rates\n"
            "   • Complete attendance records\n"
            "   • Day-by-day breakdown\n"
            "   • One-click download\n\n"
            "**🔐 Data Security:**\n"
            "   • Securely stored\n"
            "   • Private to your account\n"
            "   • Encrypted database\n\n"
            "═══════════════════════════════════════\n\n"
            "**To Export PDF:**\n"
            "1. Go to Tuition page\n"
            "2. Click 'Export Routine PDF'\n"
            "3. PDF downloads automatically!"
        )
    
    # ===== Current Status (personalized) =====
    if re.search(r'\b(my|current|status|summary|stats?|spending)\b', msg):
        response = f"Here's your quick status, {display_name}:\n\n"
        response += f"💰 This week: ৳{total_recent:,.0f}\n"
        response += f"💰 All-time total: ৳{total_all_time:,.0f}\n"
        if category_str:
            response += f"📊 Top spending: {category_str}\n"
        if tuition_income > 0:
            response += f"🎓 Tuition income potential: ৳{tuition_income:,.0f} ({tuition_progress}% done)\n"
        if group_count > 0:
            response += f"👥 Active groups: {group_count}\n"
        response += "\nCheck your Dashboard for detailed insights!"
        return response
    
    # ===== Thanks / Appreciation =====
    if re.search(r'\b(thanks?|thank\s+you|appreciate|helpful)\b', msg):
        return (
            f"You're very welcome, {display_name}! 😊 I'm always here to help you navigate FeinBuddy. "
            "Feel free to ask anything else about the app's features or how to use them!"
        )
    
    # ===== Default fallback for unknown queries =====
    return (
        "I'm not quite sure about that specific query, but I'm here to help with FeinBuddy! 🤔\n\n"
        "I can assist you with:\n"
        "• What FeinBuddy does\n"
        "• How to use features (Expenses, Groups, Tuition)\n"
        "• Navigation and settings\n"
        "• Your current financial status\n\n"
        "What would you like to know?"
    )

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

# Create tables (with error handling for Vercel)
try:
    with app.app_context():
        db.create_all()
        print("Database tables created successfully")
except Exception as e:
    print(f"Warning: Database initialization issue: {e}")
    # Continue anyway - tables might already exist

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Add cache control headers for authenticated pages
@app.after_request
def add_security_headers(response):
    """Add security headers to prevent caching of sensitive pages."""
    # Only apply to authenticated routes (not static files or public pages)
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
    'MAIL_DEFAULT_SENDER') or os.environ.get('MAIL_USERNAME', 'noreply@FinBuddy.com')

mail = Mail(app)

# Initialize SocketIO and APScheduler only for local development
if not IS_VERCEL:
    # Initialize SocketIO for real-time updates
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

    # Scheduler setup
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
else:
    # On Vercel, these features are disabled
    socketio = None
    scheduler = None


def send_reminder_email(expense_id):
    """Send a reminder email for a specific expense."""
    from routes.database import Expense, User
    
    with app.app_context():
        expense = Expense.query.get(expense_id)
        if not expense or expense.reminder_sent:
            return
        
        user = User.query.get(expense.user_id)
        if not user or not user.profile:
            return
        
        email = user.profile.email
        if not email:
            return
        
        try:
            # Create email message
            msg = Message(
                subject=f'Reminder: {expense.category} - {expense.name}',
                recipients=[email],
                html=f'''
                <html>
                    <head>
                        <style>
                            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                      color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
                            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                            .expense-details {{ background: white; padding: 20px; border-radius: 8px; 
                                               margin: 20px 0; border-left: 4px solid #667eea; }}
                            .amount {{ font-size: 24px; font-weight: bold; color: #667eea; }}
                            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h1>💰 Payment Reminder</h1>
                            </div>
                            <div class="content">
                                <p>Hello {user.username},</p>
                                <p>This is a friendly reminder about your upcoming {expense.category.lower()}:</p>
                                
                                <div class="expense-details">
                                    <h2>{expense.name}</h2>
                                    <p><strong>Category:</strong> {expense.category}</p>
                                    <p><strong>Amount:</strong> <span class="amount">${expense.amount:.2f}</span></p>
                                    {f'<p><strong>Description:</strong> {expense.description}</p>' if expense.description else ''}
                                    {f'<p><strong>Note:</strong> {expense.reminder_note}</p>' if expense.reminder_note else ''}
                                </div>
                                
                                <p>Please make sure to process this payment on time.</p>
                                
                                <div class="footer">
                                    <p>This is an automated reminder from FeinBuddy Money Manager</p>
                                </div>
                            </div>
                        </div>
                    </body>
                </html>
                '''
            )
            
            mail.send(msg)
            
            # Mark as sent
            expense.reminder_sent = True
            db.session.commit()
            
        except Exception as e:
            print(f'Error sending reminder email: {str(e)}')


def schedule_reminder_email(expense_id, reminder_datetime):
    """Schedule a reminder email for a specific datetime."""
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


@scheduler.task('interval', id='check_reminders', minutes=15)
def check_and_send_reminders():
    """Periodic job to check for due reminders and send them."""
    from datetime import datetime, timezone
    from routes.database import Expense
    
    with scheduler.app.app_context():
        now = datetime.now(timezone.utc)
        
        # Find expenses with reminders that are due and not yet sent
        due_expenses = Expense.query.filter(
            Expense.reminder_at <= now,
            Expense.reminder_sent == False,
            Expense.reminder_at.isnot(None)
        ).all()
        
        for expense in due_expenses:
            send_reminder_email(expense.id)


def _username_maybe_email(username: str) -> bool:
    return isinstance(username, str) and '@' in username and '.' in username


def _week_range():
    from datetime import datetime, timedelta, timezone
    today = datetime.now(timezone.utc).date()
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

    subject = f"FinBuddy Weekly Report ({start_date} - {end_date})"
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
    week_ago = datetime.now(timezone.utc).date() - timedelta(days=7)
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

    # Prepare context for both AI and fallback
    user_context = {
        'display_name': display_name,
        'email': email,
        'profession': profession,
        'institution': institution,
        'total_recent': total_recent,
        'total_all_time': total_all_time,
        'category_str': category_str,
        'tuition_income': total_tuition_income,
        'tuition_progress': tuition_progress,
        'group_count': group_count,
        'recent_expense_count': len(recent_expenses)
    }

    # If Groq is not configured, use intelligent fallback
    if not groq_client:
        fallback_response = get_intelligent_fallback_response(user_message, user_context)
        return jsonify({'reply': fallback_response})

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
        "You are FinBuddy, a friendly personal finance assistant. "
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
        app.logger.exception("Groq call failed - falling back to intelligent response")
        # If AI fails, use intelligent fallback instead of showing error
        fallback_response = get_intelligent_fallback_response(user_message, user_context)
        return jsonify({'reply': fallback_response})


@app.route('/')
def home():
    """Show landing page for public, redirect to dashboard if authenticated."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    return render_template('landing.html')


@app.route('/toggle-email-notifications', methods=['POST'])
def toggle_email_notifications():
    """Toggle email notifications for the current user."""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        enabled = data.get('enabled', False)

        # Update user's email notification preference
        current_user.email_notifications = enabled
        db.session.commit()

        message = 'Email notifications enabled' if enabled else 'Email notifications disabled'
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/toggle-weekly-expense-report', methods=['POST'])
def toggle_weekly_expense_report():
    """Toggle weekly expense report for the current user."""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        enabled = data.get('enabled', False)

        # Update user's weekly expense report preference
        current_user.weekly_expense_report = enabled
        db.session.commit()

        message = '📊 Weekly expense reports enabled' if enabled else '📊 Weekly expense reports disabled'
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/toggle-tuition-reminder', methods=['POST'])
def toggle_tuition_reminder():
    """Toggle tuition reminder for the current user."""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        enabled = data.get('enabled', False)

        # Update user's tuition reminder preference
        current_user.tuition_reminder = enabled
        db.session.commit()

        message = '🔔 Tuition reminders enabled' if enabled else '🔔 Tuition reminders disabled'
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================
# WEBSOCKET EVENTS FOR REAL-TIME UPDATES
# ============================================

# Only register SocketIO handlers when not on Vercel
if not IS_VERCEL and socketio:
    @socketio.on('connect')
    def handle_connect():
        """Handle user connection to WebSocket"""
        if current_user.is_authenticated:
            # Join a room with user's ID for personalized updates
            join_room(f'user_{current_user.id}')
            print(f"User {current_user.username} connected")
        return True


    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle user disconnection"""
        if current_user.is_authenticated:
            leave_room(f'user_{current_user.id}')
            print(f"User {current_user.username} disconnected")


    @socketio.on('request_dashboard_update')
    def handle_dashboard_update(data):
        """Send updated dashboard data to user"""
        if not current_user.is_authenticated:
            return False

        try:
            from routes.dashboard import get_dashboard_data
            data = get_dashboard_data()
            emit('dashboard_updated', data, to=f'user_{current_user.id}')
            return True
        except Exception as e:
            print(f"Error sending dashboard update: {e}")
            return False


    @socketio.on('request_activity_update')
    def handle_activity_update(data):
        """Send updated activity feed to user"""
        if not current_user.is_authenticated:
            return False

        try:
            from routes.dashboard import get_recent_activities
            activities = get_recent_activities()
            emit('activity_updated', {
                'activities': activities}, to=f'user_{current_user.id}')
            return True
        except Exception as e:
            print(f"Error sending activity update: {e}")
            return False


    @socketio.on('request_group_update')
    def handle_group_update(data):
        """Send updated group data to user"""
        if not current_user.is_authenticated:
            return False

        try:
            from routes.group import get_group_details_data
            group_id = data.get('group_id')
            group_data = get_group_details_data(group_id)
            emit('group_updated', group_data, to=f'user_{current_user.id}')
            return True
        except Exception as e:
            print(f"Error sending group update: {e}")
            return False


    @socketio.on('join_group')
    def handle_join_group(data):
        """User joins a group room for real-time updates"""
        if not current_user.is_authenticated:
            return False

        try:
            group_id = data.get('group_id')
            # Verify user is member of group
            from routes.database import GroupMember
            is_member = GroupMember.query.filter_by(
                group_id=group_id,
                user_id=current_user.id
            ).first()

            if is_member:
                join_room(f'group_{group_id}')
                print(f"User {current_user.username} joined group room {group_id}")
                # Broadcast to group that user is viewing
                socketio.emit('user_viewing_group', {
                    'user_id': current_user.id,
                    'username': current_user.username
                }, to=f'group_{group_id}')
                return True
            return False
        except Exception as e:
            print(f"Error joining group: {e}")
            return False


    @socketio.on('leave_group')
    def handle_leave_group(data):
        """User leaves a group room"""
        if not current_user.is_authenticated:
            return False

        try:
            group_id = data.get('group_id')
            leave_room(f'group_{group_id}')
            print(f"User {current_user.username} left group room {group_id}")
            return True
        except Exception as e:
            print(f"Error leaving group: {e}")
            return False


    def broadcast_expense_update(user_id, expense_data):
        """Broadcast expense update to user's session"""
        socketio.emit('expense_added', expense_data, to=f'user_{user_id}')


    def broadcast_group_expense_update(group_id, expense_data):
        """Broadcast group expense update to all group members"""
        try:
            from routes.group import get_group_details_data, get_group_members_ids

            # Send to all group members in the group room
            group_data = get_group_details_data(group_id)
            socketio.emit('group_updated', group_data, to=f'group_{group_id}')

            # Also send to each member's personal room (if not in group room)
            member_ids = get_group_members_ids(group_id)
            for member_id in member_ids:
                socketio.emit('group_expense_added', {
                    'group_id': group_id,
                    'message': 'New expense added to your group!',
                    'expense': expense_data
                }, to=f'user_{member_id}')

            print(
                f"Group {group_id} expense update broadcasted to {len(member_ids)} members")
        except Exception as e:
            print(f"Error broadcasting group expense update: {e}")
else:
    # On Vercel, define stub functions to prevent errors
    def broadcast_expense_update(user_id, expense_data):
        """Stub function for Vercel - no real-time updates"""
        pass

    def broadcast_group_expense_update(group_id, expense_data):
        """Stub function for Vercel - no real-time updates"""
        pass


if __name__ == '__main__':
    print("=" * 50)
    print("FinBuddy - Starting Application")
    print("=" * 50)
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    if IS_VERCEL:
        print("Running in Vercel mode (no SocketIO or background tasks)")
        print("Server starting on http://0.0.0.0:5000")
        print("Press Ctrl+C to stop the server")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("Running in local development mode (with SocketIO and background tasks)")
        print("Server starting on http://localhost:5000")
        print("Press Ctrl+C to stop the server")
        socketio.run(app, debug=True, host='0.0.0.0',
                     port=5000, allow_unsafe_werkzeug=True)
