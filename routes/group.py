from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from routes.auth import login_required
from routes.database import db
from flask_login import current_user

group_bp = Blueprint('group', __name__)


@group_bp.route('/group')
@login_required
def group_list():
    """Display list of groups user is part of."""
    user_id = session.get('user_id')
    
    conn = db.session.connection()
    
    # Get all groups user is a member of
    groups = conn.execute(
        '''SELECT g.*, u.username as creator_name,
           (SELECT COUNT(*) FROM group_members WHERE group_id = g.id) as member_count
           FROM groups g
           JOIN users u ON g.created_by = u.id
           WHERE g.id IN (SELECT group_id FROM group_members WHERE user_id = ?)
           ORDER BY g.created_at DESC''',
        (user_id,)
    ).fetchall()
    
    conn.close()
    
    return render_template('group.html', groups=groups)


@group_bp.route('/group/create', methods=['POST'])
@login_required
def create_group():
    """Create a new group."""
    user_id = session.get('user_id')
    
    name = request.form.get('name')
    description = request.form.get('description', '')
    
    if not name:
        flash('Group name is required!', 'error')
        return redirect(url_for('group.group_list'))
    
    conn = db.session.connection()
    
    # Create group
    cursor = conn.execute(
        'INSERT INTO groups (name, description, created_by) VALUES (?, ?, ?)',
        (name, description, user_id)
    )
    group_id = cursor.lastrowid
    
    # Add creator as member
    conn.execute(
        'INSERT INTO group_members (group_id, user_id) VALUES (?, ?)',
        (group_id, user_id)
    )
    
    conn.commit()
    conn.close()
    
    flash('Group created successfully!', 'success')
    return redirect(url_for('group.group_detail', group_id=group_id))


@group_bp.route('/group/<int:group_id>')
@login_required
def group_detail(group_id):
    """Display group details and expenses."""
    user_id = session.get('user_id')
    
    conn = db.session.connection()
    
    # Check if user is member
    membership = conn.execute(
        'SELECT * FROM group_members WHERE group_id = ? AND user_id = ?',
        (group_id, user_id)
    ).fetchone()
    
    if not membership:
        conn.close()
        flash('You are not a member of this group!', 'error')
        return redirect(url_for('group.group_list'))
    
    # Get group info
    group = conn.execute(
        '''SELECT g.*, u.username as creator_name
           FROM groups g
           JOIN users u ON g.created_by = u.id
           WHERE g.id = ?''',
        (group_id,)
    ).fetchone()
    
    # Get members
    members = conn.execute(
        '''SELECT u.id, u.username, gm.joined_at
           FROM group_members gm
           JOIN users u ON gm.user_id = u.id
           WHERE gm.group_id = ?
           ORDER BY gm.joined_at''',
        (group_id,)
    ).fetchall()
    
    # Get expenses
    expenses = conn.execute(
        '''SELECT ge.*, u.username as paid_by_name
           FROM group_expenses ge
           JOIN users u ON ge.paid_by = u.id
           WHERE ge.group_id = ?
           ORDER BY ge.date DESC, ge.created_at DESC''',
        (group_id,)
    ).fetchall()
    
    # Calculate balances
    balances = {}
    for member in members:
        balances[member['id']] = 0
    
    for expense in expenses:
        # Get splits for this expense
        splits = conn.execute(
            'SELECT * FROM expense_splits WHERE expense_id = ?',
            (expense['id'],)
        ).fetchall()
        
        # Person who paid gets positive balance
        balances[expense['paid_by']] += expense['amount']
        
        # People who owe get negative balance
        for split in splits:
            balances[split['user_id']] -= split['share_amount']
    
    conn.close()
    
    return render_template(
        'group.html',
        group=group,
        members=members,
        expenses=expenses,
        balances=balances,
        mode='detail'
    )


@group_bp.route('/group/<int:group_id>/add_expense', methods=['POST'])
@login_required
def add_group_expense(group_id):
    """Add an expense to a group."""
    user_id = session.get('user_id')
    
    title = request.form.get('title')
    amount = request.form.get('amount')
    description = request.form.get('description', '')
    date = request.form.get('date')
    split_type = request.form.get('split_type', 'equal')
    
    # Validation
    if not all([title, amount, date]):
        flash('Please fill in all required fields!', 'error')
        return redirect(url_for('group.group_detail', group_id=group_id))
    
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except ValueError:
        flash('Invalid amount!', 'error')
        return redirect(url_for('group.group_detail', group_id=group_id))
    
    conn = db.session.connection()
    
    # Verify membership
    membership = conn.execute(
        'SELECT * FROM group_members WHERE group_id = ? AND user_id = ?',
        (group_id, user_id)
    ).fetchone()
    
    if not membership:
        conn.close()
        flash('You are not a member of this group!', 'error')
        return redirect(url_for('group.group_list'))
    
    # Get all members
    members = conn.execute(
        'SELECT user_id FROM group_members WHERE group_id = ?',
        (group_id,)
    ).fetchall()
    
    # Create expense
    cursor = conn.execute(
        '''INSERT INTO group_expenses 
           (group_id, paid_by, title, amount, description, date)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (group_id, user_id, title, amount, description, date)
    )
    expense_id = cursor.lastrowid
    
    # Create splits (equal split by default)
    share_amount = amount / len(members)
    for member in members:
        conn.execute(
            '''INSERT INTO expense_splits 
               (expense_id, user_id, share_amount, is_paid)
               VALUES (?, ?, ?, ?)''',
            (expense_id, member['user_id'], share_amount, 
             1 if member['user_id'] == user_id else 0)
        )
    
    conn.commit()
    conn.close()
    
    flash('Expense added successfully!', 'success')
    return redirect(url_for('group.group_detail', group_id=group_id))


@group_bp.route('/group/<int:group_id>/add_member', methods=['POST'])
@login_required
def add_member(group_id):
    """Add a member to a group."""
    user_id = session.get('user_id')
    username = request.form.get('username')
    
    if not username:
        flash('Username is required!', 'error')
        return redirect(url_for('group.group_detail', group_id=group_id))
    
    conn = db.session.connection()
    
    # Verify user is admin/creator
    group = conn.execute(
        'SELECT * FROM groups WHERE id = ? AND created_by = ?',
        (group_id, user_id)
    ).fetchone()
    
    if not group:
        conn.close()
        flash('Only group creator can add members!', 'error')
        return redirect(url_for('group.group_detail', group_id=group_id))
    
    # Find user by username
    new_member = conn.execute(
        'SELECT id FROM users WHERE username = ?',
        (username,)
    ).fetchone()
    
    if not new_member:
        conn.close()
        flash('User not found!', 'error')
        return redirect(url_for('group.group_detail', group_id=group_id))
    
    # Check if already member
    existing = conn.execute(
        'SELECT * FROM group_members WHERE group_id = ? AND user_id = ?',
        (group_id, new_member['id'])
    ).fetchone()
    
    if existing:
        conn.close()
        flash('User is already a member!', 'error')
        return redirect(url_for('group.group_detail', group_id=group_id))
    
    # Add member
    conn.execute(
        'INSERT INTO group_members (group_id, user_id) VALUES (?, ?)',
        (group_id, new_member['id'])
    )
    conn.commit()
    conn.close()
    
    flash('Member added successfully!', 'success')
    return redirect(url_for('group.group_detail', group_id=group_id))


@group_bp.route('/group/<int:group_id>/settle/<int:expense_id>', methods=['POST'])
@login_required
def settle_expense(group_id, expense_id):
    """Mark an expense as settled."""
    user_id = session.get('user_id')
    
    conn = db.session.connection()
    
    # Update split as paid
    conn.execute(
        '''UPDATE expense_splits 
           SET is_paid = 1 
           WHERE expense_id = ? AND user_id = ?''',
        (expense_id, user_id)
    )
    conn.commit()
    conn.close()
    
    flash('Expense marked as settled!', 'success')
    return redirect(url_for('group.group_detail', group_id=group_id))
