from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from routes.database import db, Group, GroupMember, GroupExpense, ExpenseSplit
from datetime import datetime
import random
import string

group = Blueprint("group", __name__)


def generate_join_code():
    """Generate a unique 6-character join code."""
    while True:
        code = ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=6))
        if not Group.query.filter_by(join_code=code).first():
            return code


def calculate_settlements(balances, user_names):
    """Calculate optimal settlements to balance all debts.

    Args:
        balances: dict of user_id -> balance (positive = owed, negative = owes)
        user_names: dict of user_id -> username

    Returns:
        list of dicts with 'from', 'to', 'amount' for settlements
    """
    # Separate creditors (positive balance) and debtors (negative balance)
    creditors = [(uid, bal) for uid, bal in balances.items() if bal > 0.01]
    debtors = [(uid, -bal) for uid, bal in balances.items() if bal < -0.01]

    settlements = []

    # Sort by amount for better matching
    creditors.sort(key=lambda x: x[1], reverse=True)
    debtors.sort(key=lambda x: x[1], reverse=True)

    i, j = 0, 0
    while i < len(creditors) and j < len(debtors):
        creditor_id, credit_amount = creditors[i]
        debtor_id, debt_amount = debtors[j]

        # Settle the minimum of what's owed and what's due
        settle_amount = min(credit_amount, debt_amount)

        if settle_amount > 0.01:  # Ignore very small amounts
            settlements.append({
                'from': user_names[debtor_id],
                'to': user_names[creditor_id],
                'amount': settle_amount
            })

        # Update remaining balances
        creditors[i] = (creditor_id, credit_amount - settle_amount)
        debtors[j] = (debtor_id, debt_amount - settle_amount)

        # Move to next creditor or debtor if current one is settled
        if creditors[i][1] < 0.01:
            i += 1
        if debtors[j][1] < 0.01:
            j += 1

    return settlements


@group.route('/groups')
@login_required
def my_groups():
    """View all groups the current user is a member of."""
    memberships = GroupMember.query.filter_by(user_id=current_user.id).all()
    groups = [membership.group for membership in memberships]
    return render_template('group.html', groups=groups)


@group.route('/groups/create', methods=['POST'])
@login_required
def create_group():
    """Create a new group."""
    from flask import request
    name = request.form.get('group_name')

    if not name:
        flash('Group name is required!', 'danger')
        return redirect(url_for('group.my_groups'))

    new_group = Group(name=name, created_by=current_user.id,
                      join_code=generate_join_code())
    db.session.add(new_group)
    db.session.commit()
    # Add the creator as a member
    membership = GroupMember(group_id=new_group.id, user_id=current_user.id)
    db.session.add(membership)
    db.session.commit()

    flash(f'Group "{name}" created successfully!', 'success')
    return redirect(url_for('group.group_details', group_id=new_group.id))


@group.route('/groups/join', methods=['POST'])
@login_required
def join_group():
    """Join a group using an invite code."""
    from flask import request
    join_code = request.form.get('join_code', '').strip().upper()

    if not join_code:
        flash('Please enter an invite code!', 'danger')
        return redirect(url_for('group.my_groups'))

    # Find group by join code
    group = Group.query.filter_by(join_code=join_code).first()

    if not group:
        flash(f'Invalid invite code: {join_code}', 'danger')
        return redirect(url_for('group.my_groups'))

    # Check if already a member
    existing_membership = GroupMember.query.filter_by(
        group_id=group.id, user_id=current_user.id).first()

    if existing_membership:
        flash(f'You are already a member of "{group.name}"!', 'info')
        return redirect(url_for('group.group_details', group_id=group.id))

    # Add user to group
    membership = GroupMember(group_id=group.id, user_id=current_user.id)
    db.session.add(membership)
    db.session.commit()

    flash(f'Successfully joined "{group.name}"!', 'success')
    return redirect(url_for('group.group_details', group_id=group.id))


@group.route('/groups/<int:group_id>')
@login_required
def group_details(group_id):
    """View details of a specific group."""
    from sqlalchemy import func
    group = Group.query.get_or_404(group_id)
    # Ensure the current user is a member of the group
    membership = GroupMember.query.filter_by(
        group_id=group.id, user_id=current_user.id).first()
    if not membership:
        flash('You are not a member of this group!', 'danger')
        return redirect(url_for('group.my_groups'))

    # Calculate total group expense
    total_group_expense = db.session.query(func.sum(GroupExpense.amount)).filter_by(
        group_id=group_id).scalar() or 0.0

    # Get member statistics and calculate balances
    members = []
    member_count = len(group.members)
    fair_share = total_group_expense / member_count if member_count > 0 else 0

    balances = {}  # user_id -> balance (positive = owed, negative = owes)

    for member in group.members:
        user = member.user
        # Count expenses paid by this member
        member_total = db.session.query(func.sum(GroupExpense.amount)).filter_by(
            group_id=group_id, paid_by=user.id).scalar() or 0.0
        member_count_exp = db.session.query(func.count(GroupExpense.id)).filter_by(
            group_id=group_id, paid_by=user.id).scalar() or 0

        # Calculate balance: what they paid minus their fair share
        balance = member_total - fair_share
        balances[user.id] = balance

        members.append({
            'id': user.id,
            'name': user.username,
            'total': member_total,
            'count': member_count_exp,
            'balance': balance
        })

    # Calculate settlements (who should pay whom)
    settlements = calculate_settlements(
        balances, {m['id']: m['name'] for m in members})

    expenses = group.expenses
    return render_template('groupDetails.html',
                           group=group,
                           members=members,
                           expenses=expenses,
                           total_group_expense=total_group_expense,
                           fair_share=fair_share,
                           settlements=settlements)


@group.route('/groups/<int:group_id>/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense_to_group(group_id):
    """Add a new expense to a group."""
    from flask import request
    group = Group.query.get_or_404(group_id)

    # Verify membership
    membership = GroupMember.query.filter_by(
        group_id=group_id, user_id=current_user.id).first()
    if not membership:
        flash('You are not a member of this group!', 'danger')
        return redirect(url_for('group.my_groups'))

    if request.method == 'GET':
        # Show the form to add expense
        members = [member.user for member in group.members]
        return render_template('addGroupExpense.html', group=group, members=members)

    # Handle POST - add the expense
    title = request.form.get('title')
    amount = request.form.get('amount')
    description = request.form.get('description', '')
    expense_date = request.form.get('date')

    if not all([title, amount, expense_date]):
        flash('Please fill in all required fields!', 'danger')
        return redirect(url_for('group.add_expense_to_group', group_id=group_id))

    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except ValueError:
        flash('Invalid amount!', 'danger')
        return redirect(url_for('group.add_expense_to_group', group_id=group_id))

    # Create the expense
    new_expense = GroupExpense(
        group_id=group_id,
        title=title,
        amount=amount,
        paid_by=current_user.id,
        description=description,
        date=datetime.strptime(expense_date, '%Y-%m-%d').date()
    )
    db.session.add(new_expense)
    db.session.commit()

    # Split equally among all members
    members = group.members
    share_amount = amount / len(members)

    for member in members:
        expense_split = ExpenseSplit(
            expense_id=new_expense.id,
            user_id=member.user_id,
            share_amount=share_amount,
            is_paid=(member.user_id == current_user.id)
        )
        db.session.add(expense_split)

    db.session.commit()

    flash(f'Expense "{title}" added successfully!', 'success')
    return redirect(url_for('group.group_details', group_id=group_id))


def add_member_to_group(group_id, user_id):
    """Add a new member to a group."""
    membership = GroupMember(group_id=group_id, user_id=user_id)
    db.session.add(membership)
    db.session.commit()
    return membership


def split_expense(expense_id, splits):
    """Split an expense among group members.

    Args:
        expense_id (int): The ID of the group expense.
        splits (list of tuples): Each tuple contains (user_id, share_amount).
    """
    for user_id, share_amount in splits:
        expense_split = ExpenseSplit(
            expense_id=expense_id,
            user_id=user_id,
            share_amount=share_amount
        )
        db.session.add(expense_split)
    db.session.commit()
