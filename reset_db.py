"""
Quick script to reset the database with correct schema.
Run this after stopping the Flask app.
"""
import os
import time
from app import app
from routes.database import db

# Delete old database file if exists
db_path = 'instance/database.db'

print("Attempting to reset database...")

# Try to close any existing connections first
try:
    with app.app_context():
        db.session.close_all()
        db.engine.dispose()
    print("Closed existing database connections")
except Exception as e:
    print(f"Note: {e}")

# Try deleting with multiple attempts
max_attempts = 5
for attempt in range(max_attempts):
    if os.path.exists(db_path):
        try:
            time.sleep(1)
            os.remove(db_path)
            print(f"✓ Deleted old database: {db_path}")
            break
        except PermissionError:
            if attempt < max_attempts - 1:
                print(
                    f"Attempt {attempt + 1}/{max_attempts}: Database in use, retrying...")
                time.sleep(2)
            else:
                print(
                    f"\n❌ ERROR: Could not delete {db_path} - file is still in use.")
                print("\nPossible solutions:")
                print("1. Close VS Code SQLite extension/viewer")
                print("2. Close any database browser tools")
                print("3. Manually delete the file: instance\\database.db")
                print("4. Then run this script again")
                exit(1)
        except Exception as e:
            print(f"Error: {e}")
            exit(1)
    else:
        print("No existing database found. Creating new one...")
        break

# Create new database with correct schema
with app.app_context():
    db.create_all()
    print("\n✓ Database recreated with correct schema!")
    print("✓ All tables created successfully including:")
    print("  - User, Expense, Debt, TuitionRecord, Profile")
    print("  - Group, GroupMember, GroupExpense, ExpenseSplit")
    print("\n✓ Ready to start the app with: python app.py")
    print("\nYou can now run 'python app.py' to start the server.")
