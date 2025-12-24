from flask import Blueprint, render_template, session, redirect, url_for, flash
from routes.auth import login_required
import database
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard page showing overview and recent activity."""
    user_id = session.get('user_id')
    username = session.get('username')
    
    conn = database.get_db_connection()
    
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
    
    all_activities = list(personal_activities) + list(group_activities) + list(tuition_activities)
    all_activities.sort(key=lambda x: x['created_at'], reverse=True)
    recent_activities = all_activities[:5]
    
    return render_template(
        'dashboard.html',
        username=username,
        personal_this_month=round(personal_this_month, 2),
        group_balance=round(group_balance, 2),
        pending_tuition=round(pending_tuition, 2),
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
