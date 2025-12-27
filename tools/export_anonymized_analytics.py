#!/usr/bin/env python3
"""
Anonymized Analytics Export Tool

Exports aggregated analytics data WITHOUT any personally identifiable information (PII).
This script is meant for LOCAL ANALYSIS ONLY - outputs are gitignored.

PRIVACY RULES:
- NO user_id, email, username, profile_name
- NO raw descriptions or expense names
- NO exact timestamps (only YYYY-MM buckets)
- ONLY aggregate counts and totals

Usage:
    python tools/export_anonymized_analytics.py
    
Output:
    exports/analytics_YYYYMMDD_HHMMSS.json
"""

import os
import sys
import json
from datetime import datetime
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from routes.database import db, User, Profile, Expense, TuitionRecord, Group, GroupMember, GroupExpense, Debt


def create_app():
    """Create a minimal Flask app for database access"""
    app = Flask(__name__)
    
    # Database configuration (same as main app)
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # PostgreSQL (production)
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # SQLite (local)
        basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "finance.db")}'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    return app


def export_anonymized_analytics():
    """
    Export anonymized, aggregated analytics data.
    
    Returns dict with:
    - user_statistics: total counts (no user details)
    - expense_analytics: category totals, monthly buckets
    - tuition_analytics: aggregated tuition data
    - group_analytics: group expense totals
    - debt_analytics: aggregate debt/due totals
    """
    
    analytics = {
        "export_metadata": {
            "exported_at": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "privacy_level": "anonymized_aggregates_only"
        },
        "user_statistics": {},
        "expense_analytics": {},
        "tuition_analytics": {},
        "group_analytics": {},
        "debt_analytics": {}
    }
    
    # ========== USER STATISTICS ==========
    total_users = User.query.count()
    users_with_profile = Profile.query.count()
    users_with_weekly_report = User.query.filter_by(weekly_expense_report=True).count()
    users_with_tuition_reminder = User.query.filter_by(tuition_reminder=True).count()
    
    analytics["user_statistics"] = {
        "total_users": total_users,
        "users_with_profile": users_with_profile,
        "users_with_weekly_report_enabled": users_with_weekly_report,
        "users_with_tuition_reminder_enabled": users_with_tuition_reminder
    }
    
    # ========== EXPENSE ANALYTICS ==========
    expenses = Expense.query.all()
    
    # Category totals (across ALL users - no user breakdown)
    category_totals = defaultdict(float)
    category_counts = defaultdict(int)
    
    # Monthly buckets (YYYY-MM)
    monthly_totals = defaultdict(float)
    monthly_counts = defaultdict(int)
    
    # Expense type distribution
    type_distribution = defaultdict(int)
    
    # Reminders statistics
    total_with_reminders = 0
    reminders_sent = 0
    
    for exp in expenses:
        # Category aggregation
        cat = exp.category or 'Other'
        category_totals[cat] += exp.amount
        category_counts[cat] += 1
        
        # Monthly bucket
        if exp.date:
            month_key = exp.date.strftime('%Y-%m')
            monthly_totals[month_key] += exp.amount
            monthly_counts[month_key] += 1
        
        # Type distribution
        exp_type = exp.type or 'unspecified'
        type_distribution[exp_type] += 1
        
        # Reminder stats
        if exp.reminder_at:
            total_with_reminders += 1
            if exp.reminder_sent:
                reminders_sent += 1
    
    analytics["expense_analytics"] = {
        "total_expenses": len(expenses),
        "total_amount": round(sum(e.amount for e in expenses), 2),
        "category_breakdown": {
            cat: {
                "total_amount": round(total, 2),
                "count": category_counts[cat]
            }
            for cat, total in sorted(category_totals.items())
        },
        "monthly_breakdown": {
            month: {
                "total_amount": round(total, 2),
                "count": monthly_counts[month]
            }
            for month, total in sorted(monthly_totals.items())
        },
        "type_distribution": dict(type_distribution),
        "reminder_statistics": {
            "expenses_with_reminders": total_with_reminders,
            "reminders_sent": reminders_sent
        }
    }
    
    # ========== TUITION ANALYTICS ==========
    tuition_records = TuitionRecord.query.all()
    
    total_tuition_amount = sum(t.amount for t in tuition_records)
    total_days_scheduled = sum(t.total_days for t in tuition_records)
    total_days_completed = sum(t.total_completed for t in tuition_records)
    
    analytics["tuition_analytics"] = {
        "total_tuition_records": len(tuition_records),
        "total_tuition_amount": round(total_tuition_amount, 2),
        "total_days_scheduled": total_days_scheduled,
        "total_days_completed": total_days_completed,
        "completion_rate": round(total_days_completed / total_days_scheduled * 100, 2) if total_days_scheduled > 0 else 0
    }
    
    # ========== GROUP ANALYTICS ==========
    groups = Group.query.all()
    group_expenses = GroupExpense.query.all()
    group_members = GroupMember.query.all()
    
    # Monthly group expense buckets
    group_monthly_totals = defaultdict(float)
    
    for gexp in group_expenses:
        if gexp.date:
            month_key = gexp.date.strftime('%Y-%m')
            group_monthly_totals[month_key] += gexp.amount
    
    analytics["group_analytics"] = {
        "total_groups": len(groups),
        "total_group_memberships": len(group_members),
        "total_group_expenses": len(group_expenses),
        "total_group_expense_amount": round(sum(g.amount for g in group_expenses), 2),
        "average_group_size": round(len(group_members) / len(groups), 2) if groups else 0,
        "monthly_breakdown": {
            month: round(total, 2)
            for month, total in sorted(group_monthly_totals.items())
        }
    }
    
    # ========== DEBT ANALYTICS ==========
    debts = Debt.query.all()
    
    dues = [d for d in debts if d.debt_type == 'due']  # Owed TO users
    owes = [d for d in debts if d.debt_type == 'owe']  # Users OWE others
    
    analytics["debt_analytics"] = {
        "total_debt_records": len(debts),
        "dues": {
            "count": len(dues),
            "total_amount": round(sum(d.amount for d in dues), 2)
        },
        "owes": {
            "count": len(owes),
            "total_amount": round(sum(d.amount for d in owes), 2)
        }
    }
    
    return analytics


def save_export(analytics: dict, output_dir: str = "exports") -> str:
    """Save analytics to JSON file in exports directory"""
    
    # Ensure exports directory exists
    exports_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        output_dir
    )
    os.makedirs(exports_path, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"analytics_{timestamp}.json"
    filepath = os.path.join(exports_path, filename)
    
    # Write JSON
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(analytics, f, indent=2, ensure_ascii=False)
    
    return filepath


def main():
    """Main entry point"""
    print("=" * 60)
    print("ANONYMIZED ANALYTICS EXPORT")
    print("=" * 60)
    print("\nPRIVACY: This export contains ONLY aggregated data.")
    print("         No user identifiers, emails, or names are included.\n")
    
    app = create_app()
    
    with app.app_context():
        print("Collecting anonymized analytics...")
        analytics = export_anonymized_analytics()
        
        filepath = save_export(analytics)
        
        print(f"\n✓ Export saved to: {filepath}")
        print("\nSummary:")
        print(f"  - Total users: {analytics['user_statistics']['total_users']}")
        print(f"  - Total expenses: {analytics['expense_analytics']['total_expenses']}")
        print(f"  - Total tuition records: {analytics['tuition_analytics']['total_tuition_records']}")
        print(f"  - Total groups: {analytics['group_analytics']['total_groups']}")
        print(f"  - Total debt records: {analytics['debt_analytics']['total_debt_records']}")
        print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
