"""
Unified migration script for FinBuddy Money Manager
This script adds all missing columns to the relevant tables in the database.
"""
import os
import sqlite3
from flask import Flask
from sqlalchemy import text, inspect
from routes.database import db

# --- CONFIGURATION ---
DB_PATHS = [
    os.path.join('instance', 'finance.db'),
    os.path.join('instance', 'database.db')
]


def get_existing_db():
    for path in DB_PATHS:
        if os.path.exists(path):
            return path
    return None


def migrate_sqlite():
    db_path = get_existing_db()
    if not db_path:
        print("No database found. Run the app first to create it.")
        return
    print(f"Migrating SQLite DB at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # --- Profile Table: Add email column ---
    cursor.execute("PRAGMA table_info(profile)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'email' not in columns:
        print("Adding 'email' column to profile table...")
        cursor.execute("ALTER TABLE profile ADD COLUMN email VARCHAR(120)")
        print("✓ Added 'email' column to profile table")
    else:
        print("✓ 'email' column already exists in profile table")

    # --- Expense Table: Add columns ---
    cursor.execute("PRAGMA table_info(expense)")
    columns = [row[1] for row in cursor.fetchall()]
    expense_columns = {
        'category': "VARCHAR(50) DEFAULT 'Other'",
        'description': "TEXT",
        'date': "DATE",
        'created_at': "DATETIME",
        'type': "VARCHAR(50)",
        'reminder_at': "DATETIME",
        'reminder_sent': "BOOLEAN DEFAULT 0 NOT NULL",
        'reminder_note': "TEXT"
    }
    for col, col_type in expense_columns.items():
        if col not in columns:
            print(f"Adding '{col}' column to expense table...")
            cursor.execute(f"ALTER TABLE expense ADD COLUMN {col} {col_type}")
            print(f"✓ Added '{col}' column to expense table")
        else:
            print(f"✓ '{col}' column already exists in expense table")

    # --- User Table: Add notification columns ---
    cursor.execute("PRAGMA table_info(user)")
    columns = [row[1] for row in cursor.fetchall()]
    user_columns = {
        'weekly_expense_report': 'BOOLEAN DEFAULT 0 NOT NULL',
        'tuition_reminder': 'BOOLEAN DEFAULT 0 NOT NULL'
    }
    for col, col_type in user_columns.items():
        if col not in columns:
            print(f"Adding '{col}' column to user table...")
            cursor.execute(f"ALTER TABLE user ADD COLUMN {col} {col_type}")
            print(f"✓ Added '{col}' column to user table")
        else:
            print(f"✓ '{col}' column already exists in user table")

    # --- TuitionRecord Table: Add completed_date column ---
    cursor.execute("PRAGMA table_info(tuition_record)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'completed_date' not in columns:
        print("Adding 'completed_date' column to tuition_record table...")
        cursor.execute(
            "ALTER TABLE tuition_record ADD COLUMN completed_date DATE")
        print("✓ Added 'completed_date' column to tuition_record table")
    else:
        print("✓ 'completed_date' column already exists in tuition_record table")

    conn.commit()
    conn.close()
    print("\nAll migrations complete!\n")


if __name__ == '__main__':
    migrate_sqlite()
