"""
Database migration script to add reminder fields to the expense table.
Run this script once to add the new columns to your existing database.
"""

import sqlite3
import os

# Path to your database file
DB_PATH = os.path.join('instance', 'finance.db')

def migrate_database():
    """Add reminder columns to expense table if they don't exist."""
    
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        print("Creating new database - no migration needed.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(expense)")
        columns = [column[1] for column in cursor.fetchall()]
        
        changes_made = False
        
        # Add reminder_at column if it doesn't exist
        if 'reminder_at' not in columns:
            print("Adding reminder_at column...")
            cursor.execute("ALTER TABLE expense ADD COLUMN reminder_at DATETIME")
            changes_made = True
            print("✓ Added reminder_at column")
        else:
            print("✓ reminder_at column already exists")
        
        # Add reminder_sent column if it doesn't exist
        if 'reminder_sent' not in columns:
            print("Adding reminder_sent column...")
            cursor.execute("ALTER TABLE expense ADD COLUMN reminder_sent BOOLEAN DEFAULT 0 NOT NULL")
            changes_made = True
            print("✓ Added reminder_sent column")
        else:
            print("✓ reminder_sent column already exists")
        
        # Add reminder_note column if it doesn't exist
        if 'reminder_note' not in columns:
            print("Adding reminder_note column...")
            cursor.execute("ALTER TABLE expense ADD COLUMN reminder_note TEXT")
            changes_made = True
            print("✓ Added reminder_note column")
        else:
            print("✓ reminder_note column already exists")
        
        if changes_made:
            conn.commit()
            print("\n✓ Database migration completed successfully!")
        else:
            print("\n✓ No migration needed - all columns exist")
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ Error during migration: {str(e)}")
        raise
    
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 50)
    print("FeinBuddy Money Manager - Database Migration")
    print("Adding reminder fields to expense table")
    print("=" * 50)
    print()
    
    migrate_database()
    
    print()
    print("=" * 50)
    print("Migration script completed")
    print("=" * 50)
