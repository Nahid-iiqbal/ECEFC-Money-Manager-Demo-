"""
Migrate database to add missing columns to tuition_record table
"""
import sqlite3
import os

db_path = 'instance/database.db'

if not os.path.exists(db_path):
    print("Database doesn't exist. Run the app first to create it.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Drop the old table if it exists
cursor.execute("DROP TABLE IF EXISTS tuition_record")
print("Dropped old tuition_record table")

# Create new table with correct schema
cursor.execute('''
    CREATE TABLE tuition_record (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        student_name VARCHAR(100) NOT NULL,
        total_days INTEGER NOT NULL,
        total_completed INTEGER NOT NULL,
        address VARCHAR(200) NOT NULL,
        amount FLOAT NOT NULL,
        days BLOB,
        tuition_time VARCHAR(10),
        FOREIGN KEY (user_id) REFERENCES user (id)
    )
''')
print("Created new tuition_record table with correct schema")

conn.commit()
conn.close()

print("\nDatabase migration complete!")
print("Columns: id, user_id, student_name, total_days, total_completed, address, amount, days, tuition_time")
print("\nYou can now run 'python app.py' to start the server.")
