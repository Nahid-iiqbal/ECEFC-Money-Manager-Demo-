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

# Add type column if missing
if 'type' not in columns:
    print(f"\n=== Adding type column ===")
    try:
        sql = "ALTER TABLE expense ADD COLUMN type VARCHAR(50)"
        print(f"Executing: {sql}")
        db.session.execute(text(sql))
        db.session.commit()
        print("✓ Added column: type")
        print("  Column allows NULL values for backward compatibility with existing records")
    except Exception as e:
        print(f"✗ Error adding type column: {e}")
        db.session.rollback()
else:
    print("\n=== type column already exists ===")

print("\n=== Final table structure ===")
result = db.session.execute(text("PRAGMA table_info(expense)"))
for row in result.fetchall():
    print(f"  {row[1]}: {row[2]} (nullable: {row[3] == 0})")

print("\n✅ Migration complete!")
ctx.pop()
