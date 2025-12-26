from flask import Blueprint, render_template, session, redirect, url_for, flash
from flask_login import login_required, current_user
from routes.database import db, User, Expense
from datetime import datetime, timedelta
from sqlalchemy import text, func

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard page showing overview and recent activity."""

    today = datetime.now()
    first_day_of_month = today.replace(day=1)

    # Check if expense table has required columns
    result = db.session.execute(text("PRAGMA table_info(expense)"))
    existing_columns = [row[1] for row in result.fetchall()]
    has_date_column = 'date' in existing_columns
    has_category_column = 'category' in existing_columns

    # Get personal expenses this month
    if has_date_column:
        personal_this_month = db.session.query(func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            Expense.date >= first_day_of_month
        ).scalar() or 0
    else:
        personal_this_month = 0

    # Get all-time personal expenses using raw SQL
    total_result = db.session.execute(
        text("SELECT COALESCE(SUM(amount), 0) as total FROM expense WHERE user_id = :user_id"),
        {"user_id": current_user.id}
    ).fetchone()
    total_all_time = total_result[0] if total_result else 0

    # Get recent expense activities using raw SQL
    if has_category_column and has_date_column:
        # New schema with all columns
        recent_result = db.session.execute(
            text("SELECT id, name, amount, category, description, date FROM expense WHERE user_id = :user_id ORDER BY id DESC LIMIT 5"),
            {"user_id": current_user.id}
        ).fetchall()
    else:
        # Old schema with basic columns only
        recent_result = db.session.execute(
            text("SELECT id, name, amount FROM expense WHERE user_id = :user_id ORDER BY id DESC LIMIT 5"),
            {"user_id": current_user.id}
        ).fetchall()

    recent_activities = []
    for row in recent_result:
        if has_category_column and has_date_column:
            # SQLite returns date as string, not date object
            date_value = row[5] if row[5] else 'N/A'
            activity = {
                'type': 'Personal',
                'description': row[1],  # name
                'amount': f"{row[2]:.2f}",  # amount
                'date': date_value  # date is already a string from SQLite
            }
        else:
            activity = {
                'type': 'Personal',
                'description': row[1],  # name
                'amount': f"{row[2]:.2f}",  # amount
                'date': 'N/A'
            }
        recent_activities.append(activity)

    # Placeholder for group and tuition data
    # Calculate group balances: total to get (what others owe us) and total owed (what we owe others)
    from routes.database import GroupExpense, ExpenseSplit

    # Total to get: sum of amounts we paid for group expenses
    total_to_get = db.session.query(func.sum(GroupExpense.amount)).filter(
        GroupExpense.paid_by == current_user.id
    ).scalar() or 0

    # Total owed: sum of our unpaid expense splits in group expenses
    total_owed = db.session.query(func.sum(ExpenseSplit.share_amount)).filter(
        ExpenseSplit.user_id == current_user.id,
        ExpenseSplit.is_paid == False
    ).scalar() or 0

    group_balance = total_to_get - total_owed

    # Get tuition class completion stats
    from routes.database import TuitionRecord

    tuition_records = TuitionRecord.query.filter_by(
        user_id=current_user.id).all()
    total_classes = sum(
        record.total_days for record in tuition_records) if tuition_records else 0
    completed_classes = sum(
        record.total_completed for record in tuition_records) if tuition_records else 0

    pending_tuition = 0

    # Get spending by category and monthly data
    category_data = {}
    monthly_data = {}
    is_student = False

    # Check if user is a student
    if current_user.profile and current_user.profile.grade:
        is_student = True

    # Get analytics data for all users (not just students)
    if has_category_column and has_date_column:
        # Get category spending data
        category_result = db.session.execute(
            text("""SELECT category, COALESCE(SUM(amount), 0) as total 
                    FROM expense 
                    WHERE user_id = :user_id AND category IS NOT NULL
                    GROUP BY category
                    ORDER BY total DESC"""),
            {"user_id": current_user.id}
        ).fetchall()

        for row in category_result:
            if row[0]:  # Only add if category is not None
                category_data[row[0]] = float(row[1])

        # Get monthly spending data (last 6 months)
        six_months_ago = (today - timedelta(days=180)).replace(day=1)
        monthly_result = db.session.execute(
            text("""SELECT strftime('%Y-%m', date) as month, COALESCE(SUM(amount), 0) as total
                    FROM expense
                    WHERE user_id = :user_id AND date >= :start_date
                    GROUP BY strftime('%Y-%m', date)
                    ORDER BY month ASC"""),
            {"user_id": current_user.id, "start_date": six_months_ago}
        ).fetchall()

        for row in monthly_result:
            if row[0]:  # Only add if month is not None
                # Convert YYYY-MM to readable format
                month_obj = datetime.strptime(row[0], '%Y-%m')
                month_name = month_obj.strftime('%b %Y')
                monthly_data[month_name] = float(row[1])

    return render_template('dashboard.html',
                           username=current_user.username,
                           personal_this_month=personal_this_month,
                           group_balance=group_balance,
                           total_to_get=total_to_get,
                           total_owed=total_owed,
                           balance_status='positive' if group_balance >= 0 else 'negative',
                           completed_classes=completed_classes,
                           total_classes=total_classes,
                           total_all_time=total_all_time,
                           recent_activities=recent_activities,
                           is_student=is_student,
                           category_data=category_data,
                           monthly_data=monthly_data)

    today = datetime.now()
    first_day_of_month = today.replace(day=1).strftime('%Y-%m-%d')

    personal_this_month = conn.execute(
        '''SELECT COALESCE(SUM(amount), 0) as total 
           FROM personal_expenses 
           WHERE user_id = ? AND date >= ?''',
        (user_id, first_day_of_month)
    ).fetchone()['total']

    personal_all_time = conn.execute(
        'SELECT COALESCE(SUM(amount), 0) as total FROM personal_expenses WHERE user_id = ?',
        (user_id,)
    ).fetchone()['total']

    amount_paid = conn.execute(
        '''SELECT COALESCE(SUM(amount), 0) as total 
           FROM group_expenses 
           WHERE paid_by = ?''',
        (user_id,)
    ).fetchone()['total']

    amount_owed = conn.execute(
        '''SELECT COALESCE(SUM(es.share_amount), 0) as total 
           FROM expense_splits es
           JOIN group_expenses ge ON es.expense_id = ge.id
           WHERE es.user_id = ? AND es.is_paid = 0''',
        (user_id,)
    ).fetchone()['total']

    group_balance = amount_paid - amount_owed

    pending_tuition = conn.execute(
        '''SELECT COALESCE(SUM(amount - paid_amount), 0) as total 
           FROM tuition_records 
           WHERE user_id = ? AND status != 'paid' ''',
        (user_id,)
    ).fetchone()['total']

    personal_activities = conn.execute(
        '''SELECT 'Personal' as type, title as description, amount, date, created_at
           FROM personal_expenses 
           WHERE user_id = ? 
           ORDER BY created_at DESC LIMIT 5''',
        (user_id,)
    ).fetchall()

    group_activities = conn.execute(
        '''SELECT 'Group' as type, 
                  ge.title as description, 
                  es.share_amount as amount, 
                  ge.date, 
                  ge.created_at
           FROM expense_splits es
           JOIN group_expenses ge ON es.expense_id = ge.id
           WHERE es.user_id = ?
           ORDER BY ge.created_at DESC LIMIT 5''',
        (user_id,)
    ).fetchall()

    tuition_activities = conn.execute(
        '''SELECT 'Tuition' as type, 
                  semester || ' - ' || status as description, 
                  amount as amount, 
                  due_date as date, 
                  created_at
           FROM tuition_records 
           WHERE user_id = ?
           ORDER BY created_at DESC LIMIT 5''',
        (user_id,)
    ).fetchall()

    conn.close()

    all_activities = list(personal_activities) + \
        list(group_activities) + list(tuition_activities)
    all_activities.sort(key=lambda x: x['created_at'], reverse=True)
    recent_activities = all_activities[:5]

    return render_template(
        'dashboard.html',
        username=username,
        personal_this_month=round(personal_this_month, 2),
        group_balance=round(group_balance, 2),
        total_to_get=round(total_to_get, 2),
        total_owed=round(total_owed, 2),
        completed_classes=completed_classes,
        total_classes=total_classes,
        total_all_time=round(personal_all_time, 2),
        recent_activities=recent_activities,
        balance_status='positive' if group_balance >= 0 else 'negative'
    )


@dashboard_bp.route('/quick-add-personal', methods=['GET'])
@login_required
def quick_add_personal():
    """Quick add personal expense - redirects to personal page."""
    flash('Add your personal expense below', 'info')
    return redirect(url_for('personal.personal'))


@dashboard_bp.route('/quick-add-group', methods=['GET'])
@login_required
def quick_add_group():
    """Quick add group expense - redirects to group page."""
    flash('Create or select a group to add expenses', 'info')
    return redirect(url_for('group.group_list'))


@dashboard_bp.route('/quick-add-tuition', methods=['GET'])
@login_required
def quick_add_tuition():
    """Quick add tuition - redirects to tuition page."""
    flash('Add your tuition record below', 'info')
    return redirect(url_for('tuition.tuition_list'))


# ============================================
# HELPER FUNCTIONS FOR REAL-TIME UPDATES
# ============================================

def get_dashboard_data():
    """Get all dashboard data for real-time updates"""
    if not current_user.is_authenticated:
        return {}

    today = datetime.now()
    first_day_of_month = today.replace(day=1)

    try:
        # Personal expenses this month
        result = db.session.execute(text("PRAGMA table_info(expense)"))
        existing_columns = [row[1] for row in result.fetchall()]
        has_date_column = 'date' in existing_columns

        if has_date_column:
            personal_this_month = db.session.query(func.sum(Expense.amount)).filter(
                Expense.user_id == current_user.id,
                Expense.date >= first_day_of_month
            ).scalar() or 0
        else:
            personal_this_month = 0

        # Total all-time
        total_result = db.session.execute(
            text(
                "SELECT COALESCE(SUM(amount), 0) as total FROM expense WHERE user_id = :user_id"),
            {"user_id": current_user.id}
        ).fetchone()
        total_all_time = total_result[0] if total_result else 0

        # Group balance
        from routes.group import GroupExpense, ExpenseSplit
        total_to_get = db.session.query(func.sum(GroupExpense.amount)).filter(
            GroupExpense.paid_by == current_user.id
        ).scalar() or 0

        total_owed = db.session.query(func.sum(ExpenseSplit.share_amount)).filter(
            ExpenseSplit.user_id == current_user.id,
            ExpenseSplit.is_paid == False
        ).scalar() or 0

        group_balance = total_to_get - total_owed

        return {
            'personal_this_month': float(personal_this_month),
            'total_all_time': float(total_all_time),
            'group_balance': float(group_balance),
            'total_to_get': float(total_to_get),
            'total_owed': float(total_owed)
        }
    except Exception as e:
        print(f"Error getting dashboard data: {e}")
        return {}


def get_recent_activities():
    """Get recent activities for real-time updates"""
    if not current_user.is_authenticated:
        return []

    try:
        result = db.session.execute(
            text("SELECT id, name, amount, category, date FROM expense WHERE user_id = :user_id ORDER BY id DESC LIMIT 5"),
            {"user_id": current_user.id}
        ).fetchall()

        activities = []
        for row in result:
            activities.append({
                'id': row[0],
                'name': row[1],
                'amount': float(row[2]),
                'category': row[3] if len(row) > 3 else 'Other',
                'date': str(row[4]) if len(row) > 4 else 'N/A'
            })
        return activities
    except Exception as e:
        print(f"Error getting activities: {e}")
        return []
