"""
Migration script to add email notification settings columns to User table
"""
from app import app, db
from routes.database import User
from sqlalchemy import text


def migrate():
    with app.app_context():
        try:
            # Check which columns exist
            result = db.session.execute(text("PRAGMA table_info(user)"))
            columns = [row[1] for row in result]

            columns_to_add = {
                'weekly_expense_report': 'BOOLEAN DEFAULT 0 NOT NULL',
                'tuition_reminder': 'BOOLEAN DEFAULT 0 NOT NULL'
            }

            for column_name, column_type in columns_to_add.items():
                if column_name not in columns:
                    print(f"Adding {column_name} column to User table...")
                    db.session.execute(text(
                        f"ALTER TABLE user ADD COLUMN {column_name} {column_type}"
                    ))
                    db.session.commit()
                    print(f"✓ Successfully added {column_name} column")
                else:
                    print(f"✓ {column_name} column already exists")

        except Exception as e:
            print(f"✗ Migration failed: {e}")
            db.session.rollback()


if __name__ == '__main__':
    migrate()
