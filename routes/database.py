from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model, UserMixin):
    """User model"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True, nullable=False)
    password_hash = db.Column(db.String(80), nullable=False)
    weekly_expense_report = db.Column(
        db.Boolean, default=False, nullable=False)
    tuition_reminder = db.Column(db.Boolean, default=False, nullable=False)
    expenses = db.relationship(
        'Expense', backref='user', lazy=True, cascade='all, delete-orphan')
    debts = db.relationship('Debt', backref='user',
                            lazy=True, cascade='all, delete-orphan')
    profile = db.relationship(
        'Profile', backref='user', uselist=False, cascade='all, delete-orphan')


class Expense(db.Model):
    """Expense model for personal expenses"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=True, default='Other')
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=True, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    type = db.Column(db.String(50), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Debt(db.Model):
    """Debt model for tracking dues (owed to me) and owes (I owe others)"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    debt_type = db.Column(db.String(10), nullable=False)  # 'due' or 'owe'
    person = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    note = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=True, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)


class TuitionRecord(db.Model):
    """Tuition Record model"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    student_name = db.Column(db.String(100), nullable=False)
    total_days = db.Column(db.Integer, nullable=False)
    total_completed = db.Column(db.Integer, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    days = db.Column(db.PickleType, nullable=True)
    tuition_time = db.Column(db.String(10), nullable=True)


class Profile(db.Model):
    """Profile model for user profiles"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.id'), unique=True, nullable=False)
    profile_name = db.Column(db.String(100), nullable=False)
    picture_filename = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    profession = db.Column(db.String(100), nullable=False)
    institution = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    grade = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)


class TuitionReschedule(db.Model):
    """TuitionReschedule model for tracking class rescheduling history"""
    id = db.Column(db.Integer, primary_key=True)
    tuition_id = db.Column(db.Integer, db.ForeignKey(
        'tuition_record.id'), nullable=False)
    original_date = db.Column(db.Date, nullable=False)
    new_date = db.Column(db.Date, nullable=False)
    original_time = db.Column(db.String(10), nullable=False)
    new_time = db.Column(db.String(10), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    # pending, confirmed, cancelled
    reschedule_status = db.Column(
        db.String(20), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)

    tuition = db.relationship('TuitionRecord', backref='reschedules')


class Group(db.Model):
    """Group model for group expenses"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    join_code = db.Column(db.String(10), unique=True, nullable=True)
    created_by = db.Column(
        db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    members = db.relationship(
        'GroupMember', backref='group', lazy=True, cascade='all, delete-orphan')
    expenses = db.relationship(
        'GroupExpense', backref='group', lazy=True, cascade='all, delete-orphan')


class GroupMember(db.Model):
    """Group Member model"""
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    joined_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user = db.relationship('User', backref='group_memberships', lazy=True)


class GroupExpense(db.Model):
    """Group Expense model"""
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=True, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    paid_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    payer = db.relationship('User', backref='group_expenses_paid', lazy=True)
    splits = db.relationship(
        'ExpenseSplit', backref='group_expense', lazy=True, cascade='all, delete-orphan')


class ExpenseSplit(db.Model):
    """Expense Split model for group expenses"""
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(
        db.Integer, db.ForeignKey('group_expense.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    share_amount = db.Column(db.Float, nullable=False)
    is_paid = db.Column(db.Boolean, nullable=False, default=False)


def init_db(app):
    """Initialize the database"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
