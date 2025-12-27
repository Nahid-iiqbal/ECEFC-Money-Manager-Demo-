"""
Migration script to add completed_date column to TuitionRecord.
"""
from routes.database import db
from flask import Flask


def migrate():
    app = Flask(__name__)
    import os
    # Try to load config from file, else fallback to app.py logic
    config_path = os.path.join(os.path.dirname(
        __file__), 'instance', 'config.py')
    db_path = None
    if os.path.exists(config_path):
        app.config.from_pyfile(config_path, silent=True)
        db_path = app.config.get('SQLALCHEMY_DATABASE_URI')
    else:
        # Match app.py: prefer finance.db if it exists, else database.db
        base_dir = os.path.dirname(__file__)
        finance_db = os.path.join(base_dir, 'instance', 'finance.db')
        default_db = os.path.join(base_dir, 'database.db')
        if os.path.exists(finance_db):
            db_uri = f'sqlite:///{finance_db}'
        else:
            db_uri = f'sqlite:///{default_db}'
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db_path = db_uri
    print(f"Using database: {db_path}")
    db.init_app(app)
    with app.app_context():
        # Add completed_date column if it doesn't exist
        from sqlalchemy import inspect, Column, Date
        inspector = inspect(db.engine)
        columns = [col['name']
                   for col in inspector.get_columns('tuition_record')]
        if 'completed_date' not in columns:
            from sqlalchemy import text
            db.session.execute(
                text('ALTER TABLE tuition_record ADD COLUMN completed_date DATE'))
            db.session.commit()
            print('Added completed_date column to tuition_record.')
        else:
            print('completed_date column already exists.')


if __name__ == '__main__':
    migrate()
