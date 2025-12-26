from routes.database import db
from app import app
from sqlalchemy import inspect, text

# This migration adds the 'email' column to the 'profile' table if it does not exist.


def migrate():
    with app.app_context():
        # Ensure tables exist according to current models (for fresh DBs)
        db.create_all()

        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        if 'profile' not in tables:
            # Fresh DB, create_all should have created it with 'email'
            print("Table 'profile' not found after create_all; nothing to migrate.")
            return

        columns = [col['name'] for col in inspector.get_columns('profile')]
        if 'email' not in columns:
            print('Adding email column to profile table...')
            db.session.execute(
                text('ALTER TABLE profile ADD COLUMN email VARCHAR(120)'))
            db.session.commit()
            print('Done.')
        else:
            print('Column email already exists on profile. Skipping.')


if __name__ == '__main__':
    migrate()
