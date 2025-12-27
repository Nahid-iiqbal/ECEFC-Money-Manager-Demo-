from app import app
from routes.database import db
from sqlalchemy import text
import os

ctx = app.app_context()
ctx.push()

print(f"=== Database Location ===")
print(f"URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
print(f"Full path: {os.path.abspath(db_path)}")

print("\n=== Checking expense table structure ===")
result = db.session.execute(text("PRAGMA table_info(expense)"))
columns = [row[1] for row in result.fetchall()]
print(f"Current columns: {columns}")

# Add missing columns
columns_to_add = []
if 'category' not in columns:
    columns_to_add.append(("category", "VARCHAR(50) DEFAULT 'Other'"))
if 'description' not in columns:
    columns_to_add.append(("description", "TEXT"))
if 'date' not in columns:
    columns_to_add.append(("date", "DATE"))
if 'created_at' not in columns:
    columns_to_add.append(("created_at", "DATETIME"))
if 'type' not in columns:
    columns_to_add.append(("type", "VARCHAR(50)"))

if columns_to_add:
    print(f"\n=== Adding {len(columns_to_add)} missing columns ===")
    for col_name, col_type in columns_to_add:
        try:
            sql = f"ALTER TABLE expense ADD COLUMN {col_name} {col_type}"
            print(f"Executing: {sql}")
            db.session.execute(text(sql))
            db.session.commit()
            print(f"✓ Added column: {col_name}")
        except Exception as e:
            print(f"✗ Error adding {col_name}: {e}")
            db.session.rollback()

    # Update NULL values with current date
    print("\n=== Updating NULL dates ===")
    try:
        db.session.execute(
            text("UPDATE expense SET date = DATE('now') WHERE date IS NULL"))
        db.session.execute(
            text("UPDATE expense SET created_at = DATETIME('now') WHERE created_at IS NULL"))
        db.session.commit()
        print("✓ Updated NULL dates to current date")
    except Exception as e:
        print(f"✗ Error updating dates: {e}")
        db.session.rollback()
else:
    print("\n✓ All columns already exist!")

print("\n=== Updated table structure ===")
result = db.session.execute(text("PRAGMA table_info(expense)"))
for row in result.fetchall():
    print(f"Column: {row[1]}, Type: {row[2]}, Default: {row[4]}")

print("\n=== Verifying expenses ===")
result = db.session.execute(text("SELECT * FROM expense"))
for row in result:
    print(dict(row._mapping))

ctx.pop()
print("\n✓ Migration complete! Restart your Flask app.")

ctx = app.app_context()
ctx.push()

print(f"=== Database Location ===")
print(f"URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
print(f"Full path: {os.path.abspath(db_path)}")

print("\n=== Checking expense table structure ===")
result = db.session.execute(text("PRAGMA table_info(expense)"))
columns = [row[1] for row in result.fetchall()]
print(f"Current columns: {columns}")

# Add missing columns
columns_to_add = []
if 'category' not in columns:
    columns_to_add.append(("category", "VARCHAR(50) DEFAULT 'Other'"))
if 'description' not in columns:
    columns_to_add.append(("description", "TEXT"))
if 'date' not in columns:
    columns_to_add.append(("date", "DATE"))
if 'created_at' not in columns:
    columns_to_add.append(("created_at", "DATETIME"))
if 'type' not in columns:
    columns_to_add.append(("type", "VARCHAR(50)"))

if columns_to_add:
    print(f"\n=== Adding {len(columns_to_add)} missing columns ===")
    for col_name, col_type in columns_to_add:
        try:
            sql = f"ALTER TABLE expense ADD COLUMN {col_name} {col_type}"
            print(f"Executing: {sql}")
            db.session.execute(text(sql))
            db.session.commit()
            print(f"✓ Added column: {col_name}")
        except Exception as e:
            print(f"✗ Error adding {col_name}: {e}")
            db.session.rollback()

    # Update NULL values with current date
    print("\n=== Updating NULL dates ===")
    try:
        db.session.execute(
            text("UPDATE expense SET date = DATE('now') WHERE date IS NULL"))
        db.session.execute(
            text("UPDATE expense SET created_at = DATETIME('now') WHERE created_at IS NULL"))
        db.session.commit()
        print("✓ Updated NULL dates to current date")
    except Exception as e:
        print(f"✗ Error updating dates: {e}")
        db.session.rollback()
else:
    print("\n✓ All columns already exist!")

print("\n=== Updated table structure ===")
result = db.session.execute(text("PRAGMA table_info(expense)"))
for row in result.fetchall():
    print(f"Column: {row[1]}, Type: {row[2]}, Default: {row[4]}")

print("\n=== Verifying expenses ===")
result = db.session.execute(text("SELECT * FROM expense"))
for row in result:
    print(dict(row._mapping))

ctx.pop()
print("\n✓ Migration complete! Restart your Flask app.")
