from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from routes.database import db, Expense, Debt, Group, GroupMember, GroupExpense
from datetime import datetime
from sqlalchemy import extract, func, text

expense = Blueprint("expense", __name__)


@expense.route('/debug_expenses')
@login_required
def debug_expenses():
    """Debug route to check expense data."""
    result = db.session.execute(text(
        "SELECT * FROM expense WHERE user_id = :user_id"), {"user_id": current_user.id})
    expenses = []
    for row in result:
        expenses.append(dict(row._mapping))
    return {"expenses": expenses}


@expense.route('/personal')
@login_required
def personal():
    """Display personal expenses list."""
    # Get database column info to check which columns exist
    result = db.session.execute(text("PRAGMA table_info(expense)"))
    existing_columns = [row[1] for row in result.fetchall()]

    # Query based on available columns
    if 'category' in existing_columns and 'date' in existing_columns:
        # New schema - use ORM
        user_expenses = Expense.query.filter_by(
            user_id=current_user.id).order_by(Expense.id.desc()).all()
    else:
        # Old schema - use raw SQL to query only existing columns
        query = text(
            "SELECT id, name, amount, user_id FROM expense WHERE user_id = :user_id ORDER BY id DESC")
        result = db.session.execute(query, {"user_id": current_user.id})

        # Convert to objects with attributes
        class SimpleExpense:
            def __init__(self, id, name, amount, user_id):
                self.id = id
                self.name = name
                self.amount = amount
                self.user_id = user_id
                self.category = 'Other'
                self.description = None
                self.date = None
                self.created_at = None

        user_expenses = [SimpleExpense(*row) for row in result.fetchall()]

    total = sum(exp.amount for exp in user_expenses)

    # Category breakdown
    category_totals = {}
    for exp in user_expenses:
        category = getattr(exp, 'category', 'Other') or 'Other'
        category_totals[category] = category_totals.get(
            category, 0) + exp.amount

    return render_template(
        "expenses.html",
        expenses=user_expenses,
        total=total,
        category_totals=category_totals
    )


@expense.route('/personal/add', methods=['GET'])
@login_required
def add_expense_form():
    """Display add expense form."""
    # Get groups the current user is a member of
    user_groups = db.session.query(Group).join(
        GroupMember, Group.id == GroupMember.group_id
    ).filter(GroupMember.user_id == current_user.id).all()

    # Get query params for auto-selection
    expense_type = request.args.get('type', '')
    group_id = request.args.get('group_id', '')

    # Validate group_id if provided
    if group_id:
        try:
            group_id = int(group_id)
            # Verify user is a member
            is_member = any(g.id == group_id for g in user_groups)
            if not is_member:
                flash('You are not a member of that group!', 'danger')
                group_id = ''
        except ValueError:
            group_id = ''

    return render_template('addExpense.html',
                           today=datetime.now().strftime('%Y-%m-%d'),
                           user_groups=user_groups,
                           expense_type=expense_type,
                           preselected_group_id=group_id)


@expense.route('/expenses')
@login_required
def view_expenses():
    """Redirect to personal expenses."""
    return redirect(url_for('expense.personal'))


@expense.route('/personal/add', methods=['POST'])
@login_required
def add_expense():
    """Add a new personal or group expense."""
    try:
        name = request.form.get('name') or request.form.get('title')
        amount = float(request.form.get('amount', 0))

        # Check which columns exist in the database
        result = db.session.execute(text("PRAGMA table_info(expense)"))
        existing_columns = [row[1] for row in result.fetchall()]

        if 'category' in existing_columns:
            # New schema - use ORM with all fields
            category = request.form.get('category', 'Other')
            description = request.form.get('description', '')
            date_str = request.form.get('date')
            expense_type = request.form.get('type', '')
            group_id = request.form.get('group_id')

            # Handle reminder fields (only for Bills, Monthly Bill, Dues, Owes)
            reminder_at_str = request.form.get('reminder_at', '')
            reminder_note = request.form.get('reminder_note', '')
            reminder_at = None

            # Only process reminder if category supports it
            reminder_categories = ['Bills', 'Monthly Bill', 'Dues', 'Owes']
            if category in reminder_categories and reminder_at_str:
                try:
                    reminder_at = datetime.strptime(
                        reminder_at_str, '%Y-%m-%dT%H:%M')
                except ValueError:
                    flash('Invalid reminder date format. Reminder not set.', 'warning')

            # Parse date
            if date_str:
                expense_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                expense_date = datetime.utcnow().date()

            # Handle group expense
            if expense_type == 'Group' and group_id:
                # Verify user is a member of this group
                group_member = GroupMember.query.filter_by(
                    group_id=int(group_id),
                    user_id=current_user.id
                ).first()

                if not group_member:
                    flash('You are not a member of this group!', 'danger')
                    return redirect(url_for('expense.add_expense_form'))

                # Create group expense
                new_group_expense = GroupExpense(
                    group_id=int(group_id),
                    title=name,
                    amount=amount,
                    description=description,
                    date=expense_date,
                    paid_by=current_user.id
                )
                db.session.add(new_group_expense)
                db.session.flush()  # Get the ID

                # Create expense split for the payer
                from routes.database import ExpenseSplit
                expense_split = ExpenseSplit(
                    expense_id=new_group_expense.id,
                    user_id=current_user.id,
                    share_amount=amount,
                    is_paid=True
                )
                db.session.add(expense_split)

                flash('Group expense added successfully!', 'success')
                db.session.commit()

                # Broadcast real-time update to all group members
                try:
                    from app import broadcast_group_expense_update
                    broadcast_group_expense_update(int(group_id), {
                        'name': name,
                        'amount': float(amount),
                        'category': category,
                        'type': 'Group',
                        'date': str(expense_date),
                        'paid_by_user': current_user.username
                    })
                except Exception as e:
                    print(f"Error broadcasting group expense update: {e}")

                return redirect(url_for('group.group_details', group_id=int(group_id)))
            else:
                # Handle personal expense
                expense_data = {
                    'name': name,
                    'amount': amount,
                    'category': category,
                    'description': description,
                    'type': expense_type,
                    'user_id': current_user.id,
                    'reminder_at': reminder_at,
                    'reminder_note': reminder_note if reminder_at else None,
                    'reminder_sent': False,
                    'date': expense_date
                }

                new_expense = Expense(**expense_data)
                db.session.add(new_expense)
                db.session.commit()

                # Schedule email reminder if set
                if reminder_at and reminder_at > datetime.utcnow():
                    from app import schedule_reminder_email
                    schedule_reminder_email(new_expense.id, reminder_at)
                    flash(
                        f"Expense added with reminder set for {reminder_at.strftime('%Y-%m-%d %H:%M')}", 'success')
                else:
                    flash('Expense added successfully!', 'success')

                # Broadcast real-time update
                try:
                    from app import broadcast_expense_update
                    broadcast_expense_update(current_user.id, {
                        'name': name,
                        'amount': float(amount),
                        'category': category,
                        'type': expense_type or 'Personal',
                        'date': str(expense_date)
                    })
                except Exception as e:
                    print(f"Error broadcasting expense update: {e}")
        else:
            # Old schema - use raw SQL with only basic columns
            query = text(
                "INSERT INTO expense (name, amount, user_id) VALUES (:name, :amount, :user_id)")
            db.session.execute(query, {
                "name": name,
                "amount": amount,
                "user_id": current_user.id
            })
            db.session.commit()
            flash('Expense added successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error adding expense: {str(e)}', 'danger')

    return redirect(url_for('expense.personal'))


@expense.route('/personal/add_debt', methods=['POST'])
@login_required
def add_debt():
    """Add a new debt record (due or owe)."""
    try:
        debt_type = request.form.get('debt_type')
        person = request.form.get('person')
        amount = float(request.form.get('amount', 0))
        note = request.form.get('note', '')
        date_str = request.form.get('date')
        reminder_date_str = request.form.get('reminder_date')

        if not debt_type or not person or amount <= 0:
            flash('Please fill in all required fields with valid values.', 'danger')
            return redirect(url_for('expense.add_expense_form'))

        if debt_type not in ['due', 'owe']:
            flash('Invalid debt type selected.', 'danger')
            return redirect(url_for('expense.add_expense_form'))

        debt_data = {
            'user_id': current_user.id,
            'debt_type': debt_type,
            'person': person,
            'amount': amount,
            'note': note
        }

        if date_str:
            debt_data['date'] = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            debt_data['date'] = datetime.utcnow().date()

        # Only set reminder for dues
        if reminder_date_str and debt_type == 'due':
            debt_data['reminder_date'] = datetime.strptime(
                reminder_date_str, '%Y-%m-%d').date()

        new_debt = Debt(**debt_data)
        db.session.add(new_debt)
        db.session.commit()

        debt_label = 'Due' if debt_type == 'due' else 'Owe'
        flash(f'{debt_label} record added successfully!', 'success')
    except ValueError as ve:
        db.session.rollback()
        flash('Invalid amount format. Please enter a valid number.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding record: {str(e)}', 'danger')

    return redirect(url_for('expense.personal'))


@expense.route('/add_expense', methods=['POST'])
@login_required
def add_expense_legacy():
    """Legacy route for adding expenses."""
    return add_expense()


@expense.route("/clear_expenses", methods=['POST'])
@login_required
def clear_expenses():
    """Delete all expenses for current user."""
    try:
        Expense.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        flash('All expenses cleared!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error clearing expenses: {str(e)}', 'danger')

    return redirect(url_for('expense.personal'))


@expense.route('/expenses_pop', methods=['POST'])
@login_required
def clear_pop_expense():
    """Delete a specific expense."""
    return delete_expense()


@expense.route('/personal/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id=None):
    """Delete a specific personal expense."""
    try:
        if expense_id is None:
            expense_id = int(request.form.get('id'))

        # Use raw SQL to avoid querying columns that might not exist
        delete_query = text(
            "DELETE FROM expense WHERE id = :expense_id AND user_id = :user_id")
        result = db.session.execute(
            delete_query, {"expense_id": expense_id, "user_id": current_user.id})
        db.session.commit()

        if result.rowcount > 0:
            flash('Expense deleted successfully!', 'success')
        else:
            flash('Expense not found!', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting expense: {str(e)}', 'danger')

    return redirect(url_for('expense.personal'))


@expense.route('/personal/update/<int:expense_id>', methods=['POST'])
@login_required
def update_expense(expense_id):
    """Update an existing personal expense."""
    try:
        expense_to_update = Expense.query.filter_by(
            id=expense_id,
            user_id=current_user.id
        ).first()

        if expense_to_update:
            expense_to_update.name = request.form.get(
                'name', expense_to_update.name)
            expense_to_update.amount = float(
                request.form.get('amount', expense_to_update.amount))
            expense_to_update.category = request.form.get(
                'category', expense_to_update.category)
            expense_to_update.description = request.form.get(
                'description', expense_to_update.description)

            date_str = request.form.get('date')
            if date_str:
                expense_to_update.date = datetime.strptime(
                    date_str, '%Y-%m-%d').date()

            db.session.commit()
            flash('Expense updated successfully!', 'success')
        else:
            flash('Expense not found!', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating expense: {str(e)}', 'danger')

    return redirect(url_for('expense.personal'))


@expense.route('/personal/stats')
@login_required
def expense_stats():
    """View expense statistics and analytics."""
    user_expenses = Expense.query.filter_by(user_id=current_user.id).all()

    # Monthly totals
    monthly_totals = db.session.query(
        extract('year', Expense.date).label('year'),
        extract('month', Expense.date).label('month'),
        func.sum(Expense.amount).label('total')
    ).filter_by(user_id=current_user.id).group_by('year', 'month').all()

    # Category totals
    category_totals = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('total'),
        func.count(Expense.id).label('count')
    ).filter_by(user_id=current_user.id).group_by(Expense.category).all()

    return render_template(
        'expense_stats.html',
        monthly_totals=monthly_totals,
        category_totals=category_totals,
        total_expenses=sum(exp.amount for exp in user_expenses)
    )
