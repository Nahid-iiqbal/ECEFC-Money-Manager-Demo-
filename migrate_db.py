"""
Migrate database to add missing columns
"""
import sqlite3
import os

db_path = 'instance/database.db'

if not os.path.exists(db_path):
    print("Database doesn't exist. Run the app first to create it.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("="*60)
print("Database Migration Starting")
print("="*60)

# Check if email column exists in profile table
cursor.execute("PRAGMA table_info(profile)")
columns = [row[1] for row in cursor.fetchall()]

if 'email' not in columns:
    print("\n[Profile Table] Adding 'email' column...")
    cursor.execute("ALTER TABLE profile ADD COLUMN email VARCHAR(120)")
    print("✓ Added 'email' column to profile table")
else:
    print("\n[Profile Table] ✓ 'email' column already exists")

conn.commit()
conn.close()

print("\n" + "="*60)
print("Database migration complete!")
print("="*60)
print("\nYou can now run the app successfully.")

