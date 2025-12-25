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
if os.path.exists(db_path):
    try:
        time.sleep(1)  # Wait for any processes to release the file
        os.remove(db_path)
        print(f"Deleted old database: {db_path}")
    except PermissionError:
        print(f"Warning: Could not delete {db_path} - file is in use.")
        print("Please close all applications using the database and try again.")
        exit(1)
    except FileNotFoundError:
        print("Database file already deleted.")
else:
    print("No existing database found. Creating new one...")

# Create new database with correct schema
with app.app_context():
    db.create_all()
    print("Database recreated with correct schema!")
    print("TuitionRecord table created with columns: id, user_id, student_name, total_days, total_completed, address, amount")
    print("\nYou can now run 'python app.py' to start the server.")
