from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model, UserMixin):
    """User model"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True, nullable=False)
    password_hash = db.Column(db.String(80), nullable=False)
    expenses = db.relationship('Expense', backref='user', lazy=True, cascade='all, delete-orphan')

class Expense(db.Model):
    """Expense model for personal expenses"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False, default='Other')
    description = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

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


def init_db(app):
    """Initialize the database"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
